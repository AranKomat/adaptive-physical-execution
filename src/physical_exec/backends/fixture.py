"""Deterministic SOFTWARE FIXTURE. Not a robot simulator or learned policy.

It injects a simple state disturbance to test memory/receipts/artifact handling.
A passing fixture is NEVER evidence of manipulation/task success.
"""
from __future__ import annotations
from uuid import uuid4
import time
import numpy as np
from PIL import Image, ImageDraw
from ..contracts import Observation, ActionChunk, ExecutionReceipt, StepResult, Evaluation, Usage
from ..controllers.ports import Proposal
from ..errors import InputRejected
from ..geometry import integrate_world_deltas
from ..providers.responses import ModelReply
from ..safety import Limits, validate_chunk


class FixtureEnvironment:
    def __init__(self, limits: Limits | None = None, disturb_at: int = 2, complete_after: int = 12):
        self.limits = limits or Limits()
        self.disturb_at, self.complete_after = disturb_at, complete_after
        self._seen = {}; self.seq = 0
        self.episode_id = "uninitialized"
        self.pose = np.array([.4, 0., .4, 1., 0., 0., 0.])
        self.joints = np.zeros(7); self.open = 1.

    def _observe(self):
        im = Image.new("RGB", (640, 360), (24, 28, 35)); d = ImageDraw.Draw(im)
        d.text((20, 20), "SOFTWARE FIXTURE - NOT PHYSICS / NOT A ROBOT RESULT", fill="white")
        d.text((20, 50), f"Control step: {self.seq} | end effector x: {self.pose[0]:.3f}", fill="white")
        x = int((self.pose[0]-.25)*1200)
        d.rectangle((x, 140, x+40, 190), outline="white", width=3)
        d.line((20, 250, 620, 250), fill="white")
        return Observation(self.episode_id, self.seq, self.seq/15, "Exercise the software fixture, not a physical task.",
                           "fixture_arm", {"main": np.asarray(im)}, self.joints,
                           tuple(f"joint{i}" for i in range(7)), self.pose, self.open, 1/15,
                           eef_frame="fixture_eef")

    def reset(self, seed=0):
        self.episode_id = uuid4().hex; self.seq = 0; self._seen = {}
        self.pose = np.array([.4, 0., .4, 1., 0., 0., 0.]); self.joints = np.zeros(7); self.open = 1.
        return self._observe()

    def step(self, action: ActionChunk, command_id: str):
        if command_id in self._seen:
            previous_action, result = self._seen[command_id]
            if previous_action != action.to_dict(): raise InputRejected("command id reused with different action")
            return result  # idempotent acknowledgement, never execute twice
        original_action = action.to_dict()
        start = time.monotonic(); before = self._observe()
        action = validate_chunk(action, before, self.limits)
        count = 0
        for row in action.values:
            if action.kind == "joint_absolute":
                self.joints = row[:-1].copy(); self.pose[0] = .4 + self.joints[0]
            else:
                self.pose = row[:7].copy()
            self.open = float(row[-1]); self.seq += 1; count += 1
            if self.seq == self.disturb_at: self.pose[0] -= .02
            if self.seq >= self.complete_after: break
        after = self._observe()
        receipt = ExecutionReceipt(command_id, before.key, after.key, len(action.values), count,
                                   "executed" if count == len(action.values) else "interrupted",
                                   "fixture execution only", action.source, count/15,
                                   time.monotonic()-start)
        result = StepResult(after, receipt, self.evaluate())
        self._seen[command_id] = (original_action, result)
        return result

    def evaluate(self):
        return Evaluation(self.seq >= self.complete_after, min(self.seq/self.complete_after, 1), False,
                          "software fixture termination; not task success")

    def metadata(self):
        return {"backend": "fixture", "robot": "fixture_arm", "control_dt": 1/15,
                "physics": False, "real_hardware_supported": False,
                "time_model": "synthetic_fixture", "privileged_policy_inputs": False}

    def close(self): pass


class FixtureProposer:
    def propose(self, observation):
        values = np.repeat(np.r_[observation.joints, observation.gripper_open][None], 4, axis=0)
        values[:, 0] += np.arange(1, 5)*.01
        a = ActionChunk("joint_absolute", values, observation.key, observation.control_dt,
                        "fixture_motor", observation.joint_names, "fixture_"+uuid4().hex)
        poses = np.repeat(np.r_[observation.eef_pose, observation.gripper_open][None], 4, axis=0)
        poses[:, 0] += np.arange(1,5)*.01
        return Proposal(a, poses, "NOT A LEARNED MODEL", .0)


class FixtureProvider:
    """Deterministic Act responses used only to test orchestration."""
    def __init__(self): self.calls = 0; self.total_tokens = 0; self.usage_log = []

    def act(self, instructions, messages, schema, timeout_seconds=None):
        import json, re
        states, proposal = [], None
        for m in messages:
            for c in m.get("content", []):
                text = c.get("text", "")
                if text.startswith("<OBSERVATION>"):
                    states.append(json.loads(text[len("<OBSERVATION>"):].split("</OBSERVATION>")[0]))
                if text.startswith("<FRESH_POLICY_PROPOSAL>"):
                    proposal = json.loads(text[len("<FRESH_POLICY_PROPOSAL>"):].split("</FRESH_POLICY_PROPOSAL>")[0])
        current = states[-1]
        base = {"observation_id": current["observation_id"],
                "assessment": {"execution_status": "progressing", "intent_status": "aligned",
                               "evidence": "Synthetic fixture response; no visual reasoning occurred."}}
        if "mode" in schema["properties"]:
            base.update(proposal_id=proposal["proposal_id"], mode="accept", execute_steps=min(4, schema['properties']['execute_steps']['maximum']),
                        reason="Software fixture", translation_world=[0,0,0], rotation_world=[0,0,0],
                        gripper_override="keep", actions=[])
        else:
            spec = schema["properties"]["actions"]
            n = min(3, spec["maxItems"])
            if "delta_world" in spec["items"]["properties"]:
                actions = [{"delta_world": [.01,0,0,0,0,0], "gripper_open": 1.} for _ in range(n)]
            else:
                actions = []
                for i in range(n):
                    pose = current["eef_pose_world_xyz_wxyz"].copy(); pose[0] += .01*(i+1)
                    actions.append({"pose_world_xyz_wxyz": pose, "gripper_open": 1.})
            base.update(intent="Exercise the fixture", actions=actions)
        self.calls += 1; usage = Usage(calls=0)  # zero real API calls/tokens
        self.usage_log.append(usage)
        return ModelReply(base, usage, "fixture-"+str(self.calls))

    def close(self): pass
