"""Execution-grounded memory using RoboICL's *unmodified* anchor implementation.

The wrapper adapts cameras/single-arm actions and deliberately does not copy
provider-specific cache extensions or internal reasoning items. See SOURCE_AUDIT.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from .contracts import Observation, ActionChunk, ExecutionReceipt
from .imaging import panel, data_url, load_local_rgb
from .third_party.trajectory_memory import LiveTrajectoryMemory, omitted_interval
from .trace import dumps, verify_trace


def user_text(text: str) -> dict:
    return {"role": "user", "content": [{"type": "input_text", "text": text}]}


@dataclass(frozen=True)
class MemoryConfig:
    mode: str = "anchored"
    anchor_count: int = 25
    anchor_interval: int = 210
    max_images: int = 50
    max_text_bytes: int = 600000
    max_wire_bytes: int = 25000000
    image_edge: int = 640
    image_layout: str = "panel"

    def __post_init__(self):
        if self.mode not in ("anchored", "full"):
            raise ValueError("memory mode must be anchored or full")
        if self.image_layout not in ("panel", "separate"):
            raise ValueError("image_layout must be panel or separate")
        if self.anchor_count < 2 or self.max_images < 1 or self.image_edge < 32:
            raise ValueError("invalid memory budget")


class ExecutionMemory:
    def __init__(self, config: MemoryConfig, maximum_steps: int | None = None):
        self.config = config
        self.maximum_steps = maximum_steps
        self.reset()

    def reset(self):
        self.episode_id = None
        self.initial_sequence = 0
        self.observations: dict[int, Observation] = {}
        self.messages: dict[int, dict] = {}
        self.records: list[tuple[int, int, list]] = []
        self.rejections: list[dict] = []
        self.references: list[dict] = []
        self.summary = None
        self.anchors = LiveTrajectoryMemory(self.config.anchor_count,
                                            self.config.anchor_interval, True)
        self.anchors.configure(self.maximum_steps)

    def observe(self, observation: Observation):
        if self.episode_id is None: self.episode_id = observation.episode_id
        if observation.episode_id != self.episode_id:
            raise ValueError("cross-episode memory leak; reset memory first")
        if observation.seq in self.observations:
            prev = self.observations[observation.seq]
            if prev.key != observation.key or prev.public_state() != observation.public_state():
                raise ValueError("cannot replace committed observation")
            return
        if self.observations and observation.seq < max(self.observations):
            raise ValueError("out-of-order observation")
        self.observations[observation.seq] = observation

    def observation_message(self, seq: int) -> dict:
        if seq not in self.messages:
            o = self.observations[seq]
            content = [{"type": "input_text", "text": "<OBSERVATION>" + dumps(o.public_state()) + "</OBSERVATION>"}]
            if self.config.image_layout == "panel":
                p = panel(dict(o.images), tuple(o.images), self.config.image_edge)
                content.append({"type": "input_image", "image_url": data_url(p), "detail": "high"})
            else:
                for role, im in o.images.items():
                    content.append({"type": "input_text", "text": "Camera role: " + role})
                    content.append({"type": "input_image", "image_url": data_url(im, self.config.image_edge), "detail": "high"})
            content.append({"type": "input_text", "text": f'<OBSERVATION_END step="{seq}"/>'})
            self.messages[seq] = {"role": "user", "content": content}
        return deepcopy(self.messages[seq])

    def commit(self, before: Observation, after: Observation, action: ActionChunk,
               receipt: ExecutionReceipt, public_decision: dict):
        if receipt.observation_id != before.key or receipt.resulting_observation_id != after.key:
            raise ValueError("receipt does not match observations")
        if receipt.executed_steps <= 0:
            raise ValueError("no-execution rejections belong in the correction tail, not LIVE memory")
        if after.seq - before.seq != receipt.executed_steps:
            raise ValueError("receipt step count mismatch")
        self.observe(before); self.observe(after)
        executed = action.prefix(receipt.executed_steps).to_dict()
        # Save exact commands/receipts, not a fabricated observation of object success.
        call_id = "exec_" + receipt.command_id
        items = [{"type": "function_call", "call_id": call_id, "name": "Act",
                  "arguments": dumps(public_decision)},
                 {"type": "function_call_output", "call_id": call_id,
                  "output": dumps({"receipt": receipt.to_dict(), "executed_command": executed,
                                   "notice": "Controller feedback, not object/grasp/task verification."})}]
        summary = {"executor": action.source, "requested_steps": receipt.requested_steps,
                   "executed_steps": receipt.executed_steps,
                   "controller_status": receipt.status,
                   "intent_report": str(public_decision.get("intent", public_decision.get("reason", "")))[:1000]}
        self.anchors.capture(before.seq, after.seq, items, summary)
        self.records.append((before.seq, after.seq, items))
        self.rejections.clear()

    def reject(self, text: str):
        self.rejections.append(user_text("<NO_EXECUTION_REJECTION>" + text[:3000] +
                          " Correct the arguments at the same observation; nothing executed.</NO_EXECUTION_REJECTION>"))
        self.rejections = self.rejections[-3:]

    def set_summary(self, text: str, evidence_steps: list[int]):
        """Optional model-authored report; never promote it to measured truth."""
        if len(text) > 4000 or any(x not in self.observations for x in evidence_steps):
            raise ValueError("summary must reference observed evidence and fit its budget")
        self.summary = {"text": text, "evidence_steps": evidence_steps,
                        "provenance": "model_authored_unverified_summary"}

    def render(self, observation: Observation) -> list[dict]:
        self.observe(observation)
        if min(self.observations) != self.initial_sequence:
            raise ValueError("memory requires an explicit initial observation at sequence 0")
        if self.config.mode == "anchored":
            live = self.anchors.render(self.observation_message(self.initial_sequence), observation.seq,
                                       self.observation_message, self.rejections)
        else:
            live = [self.observation_message(self.initial_sequence)]
            for _, end, items in self.records:
                live.extend(deepcopy(items)); live.append(self.observation_message(end))
            if not self.records and observation.seq != self.initial_sequence:
                live.append(self.observation_message(observation.seq))
            live += deepcopy(self.rejections)
        messages = deepcopy(self.references)
        if self.summary is not None:
            messages.append(user_text("<UNVERIFIED_MEMORY_SUMMARY>" + dumps(self.summary) + "</UNVERIFIED_MEMORY_SUMMARY>"))
        messages += live
        enforce_context_budget(messages, self.config)
        return messages


def enforce_context_budget(messages: list[dict], cfg: MemoryConfig) -> dict:
    count = 0; text_bytes = 0
    for m in messages:
        for c in m.get("content", []):
            if c.get("type") == "input_image": count += 1
            if c.get("type") == "input_text": text_bytes += len(c.get("text", "").encode())
        text_bytes += len(str(m.get("arguments", "")).encode()) + len(str(m.get("output", "")).encode())
    wire_bytes = len(dumps(messages).encode())
    if count > cfg.max_images or text_bytes > cfg.max_text_bytes or wire_bytes > cfg.max_wire_bytes:
        raise ValueError(f"context budget exceeded: {count} images, {text_bytes} text bytes, {wire_bytes} wire bytes; explicit reconfiguration required")
    return {"images": count, "text_bytes": text_bytes, "wire_bytes": wire_bytes}


def reference_from_run(run: str | Path, expected_robot: str, expected_task: str,
                       max_chunks: int = 12, allow_related_task: bool = False,
                       expected_dt: float | None = None, expected_eef_frame: str | None = None,
                       continuation_observation_id: str | None = None) -> list[dict]:
    """Export successful simulated execution, or explicit same-episode history.

    Same robot/control contract required. Pure fixtures cannot become demonstrations.
    Budget-ended continuation history is explicitly NOT a successful demonstration.
    No exact-trajectory transfer promise. Images are checksum verified first.
    """
    if type(max_chunks) is not int or max_chunks < 1: raise ValueError("max_chunks must be positive")
    root = Path(run).resolve(); verify_trace(root)
    manifest = json.loads((root / "manifest.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if expected_dt is not None and abs(float(manifest.get("control_dt", -1))-expected_dt) > 1e-8:
        raise ValueError("reference control period mismatch")
    if expected_eef_frame is not None and manifest.get("eef_frame") != expected_eef_frame:
        raise ValueError("reference EEF frame mismatch")
    continuing = continuation_observation_id is not None
    terminal_ok = (result.get('terminal_reason') in ('decision_budget', 'control_budget', 'wall_budget')
                   if continuing else result.get('native_success', False) and result.get('terminal_reason') == 'native_success')
    if manifest.get("backend") == "fixture" or not terminal_ok or not result.get("valid_robot_result", False):
        raise ValueError("only a natively verified simulator rollout can become a reference")
    if manifest.get("robot") != expected_robot:
        raise ValueError("reference robot mismatch; explicit retargeting is not implemented")
    if not allow_related_task and manifest.get("task_instruction") != expected_task:
        raise ValueError("reference task mismatch; opt in explicitly to related-task use")
    events = [json.loads(x) for x in (root / "events.jsonl").read_text().splitlines()]
    observations = {e["data"]["observation_id"]: e["data"] for e in events if e["kind"] == "observation"}
    if continuing and list(observations)[-1] != continuation_observation_id:
        raise ValueError('continuation history ends at a different observation')
    actions = {e["data"]["command_id"]: e["data"]["action"] for e in events if e["kind"] == "execution_requested"}
    receipts = [e["data"] for e in events if e["kind"] == "execution_receipt" and e["data"]["executed_steps"] > 0]
    if not receipts: raise ValueError("no executed reference chunks")
    import numpy as np
    ids = sorted(set(np.linspace(0, len(receipts)-1, min(max_chunks, len(receipts)), dtype=int).tolist()))
    output = [user_text(
        '<CONTINUATION_HISTORY>Earlier executed chunks in THIS paused episode, NOT a successful demonstration. '
        'The prior budget ended; a new bounded budget continues at the exact final observation. '
        'TRAIN source tags below denote historical context only, not success. No evaluator labels supplied.</CONTINUATION_HISTORY>'
        if continuing else '<TRAIN_REFERENCE>Prior recorded procedure, not current geometry. Adapt all positions to current observations. No evaluator labels or reward supplied.</TRAIN_REFERENCE>')]
    prev_end = 0
    for i in ids:
        r = receipts[i]; a = actions[r["command_id"]]
        before = observations[r["observation_id"]]; after = observations[r["resulting_observation_id"]]
        if before["step"] > prev_end:
            output.append(omitted_interval("TRAIN", prev_end, before["step"]))
        for phase, o in (("before", before), ("after", after)):
            imgs = {role: load_local_rgb(root / entry["path"]) for role, entry in o["images"].items()}
            # Only already-allowlisted state. Never attach events/evaluator JSON directly.
            state = {k: v for k, v in o.items() if k != "images"}
            output.append({"role": "user", "content": [
                {"type": "input_text", "text": dumps({"source": "TRAIN", "phase": phase, "observation": state})},
                {"type": "input_image", "image_url": data_url(panel(imgs, tuple(imgs))), "detail": "high"}]})
            if phase == "before":
                cid = "reference_" + r["command_id"]
                a = {**a, "values": a["values"][:r["executed_steps"]]}
                output.extend([{"type": "function_call", "call_id": cid, "name": "Act", "arguments": dumps({"executed_command": a})},
                               {"type": "function_call_output", "call_id": cid, "output": dumps({"receipt": r})}])
        prev_end = after["step"]
    output.append(user_text("</TRAIN_REFERENCE>Begin the new LIVE episode; do not copy old scene coordinates."))
    return output
