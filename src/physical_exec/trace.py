"""Append-only audit records. Evaluator results and policy inputs stay separate."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import os
import re
import time
from typing import Any
import numpy as np
from .contracts import Observation, StepResult, ActionChunk, Usage
from .imaging import png_bytes


def jsonable(obj: Any) -> Any:
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, np.generic): return obj.item()
    if isinstance(obj, Path): return str(obj)
    if isinstance(obj, dict): return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)): return [jsonable(v) for v in obj]
    return obj


def dumps(obj: Any) -> str:
    return json.dumps(jsonable(obj), ensure_ascii=False, allow_nan=False, sort_keys=True)


def write_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(dumps(obj) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""): h.update(part)
    return h.hexdigest()


class TraceWriter:
    def __init__(self, directory: str | Path, manifest: dict):
        self.path = Path(directory).resolve()
        self.path.mkdir(parents=True, exist_ok=False)  # never overwrite a run
        self._seq = 0
        self._previous = "0"*64
        self.observations: dict[str, dict] = {}
        write_json(self.path / "manifest.json", {**manifest, "trace_schema": "physical-exec/v1",
                                                 "created_unix": time.time()})

    def event(self, kind: str, data: dict):
        payload = {"index": self._seq, "kind": kind, "data": jsonable(data),
                   "previous_sha256": self._previous}
        digest = hashlib.sha256(dumps(payload).encode()).hexdigest()
        row = {**payload, "sha256": digest}
        with (self.path / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(dumps(row)+"\n"); f.flush()
        self._seq += 1; self._previous = digest

    def observation(self, obs: Observation) -> dict:
        if obs.key in self.observations:
            return self.observations[obs.key]
        views = {}
        for role, arr in obs.images.items():
            safe = re.sub(r"[^a-zA-Z0-9_-]", "_", role)
            rel = Path("frames") / f"{obs.seq:06d}_{safe}.png"
            p = self.path / rel; p.parent.mkdir(exist_ok=True)
            if p.exists(): raise ValueError("observation file collision")
            p.write_bytes(png_bytes(arr))
            views[role] = {"path": str(rel), "sha256": sha256_file(p)}
        record = {**obs.public_state(), "images": views}
        write_json(self.path / "observations" / f"{obs.seq:06d}.json", record)
        self.event("observation", record); self.observations[obs.key] = record
        return record

    def decision(self, decision: dict, action: ActionChunk | None, usage: Usage | None):
        self.event("decision", {"public_decision": decision,
                                "action": action.to_dict() if action is not None else None,
                                "usage": asdict(usage) if usage is not None else None})

    def execution(self, result: StepResult):
        self.observation(result.observation)
        self.event("execution_receipt", result.receipt.to_dict())
        # Host-only ledger is intentionally separate from policy history.
        self.event("evaluation_host_only", asdict(result.evaluation))

    def finish(self, result: dict):
        self.event("run_finished", result)
        write_json(self.path / "result.json", {**result, "trace_sha256": self._previous})


def verify_trace(directory: str | Path, check_images: bool = True) -> dict:
    root = Path(directory).resolve(); prev = "0"*64; count = 0; final_payload = None; manifest_payload = None
    with (root / "events.jsonl").open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line); digest = row.pop("sha256")
            if row["index"] != count or row["previous_sha256"] != prev:
                raise ValueError("broken event order/hash link")
            if hashlib.sha256(dumps(row).encode()).hexdigest() != digest:
                raise ValueError("modified event payload")
            if check_images and row["kind"] == "observation":
                for image in row["data"]["images"].values():
                    p = (root / image["path"]).resolve()
                    if not p.is_relative_to(root): raise ValueError("image path escapes run")
                    if sha256_file(p) != image["sha256"]: raise ValueError("modified image")
            if row["kind"] == "run_finished": final_payload = row["data"]
            if row["kind"] == "run_manifest": manifest_payload = row["data"]
            prev = digest; count += 1
    if (root / "result.json").exists():
        result = json.loads((root / "result.json").read_text())
        expected = result.pop("trace_sha256")
        if expected != prev or final_payload != result: raise ValueError("result/trace mismatch")
    if manifest_payload is not None and json.loads((root/"manifest.json").read_text()) != manifest_payload:
        raise ValueError("manifest/trace mismatch")
    return {"events": count, "trace_sha256": prev, "images_checked": check_images}
