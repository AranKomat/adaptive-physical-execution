"""FLUX 3 Action DROID adapter. Uses absolute JOINT targets, NOT EEF deltas.

The Franka name alone does not establish distribution compatibility. Requires
three real camera views, correct joint ordering, gripper inversion, control
period qualification, and fresh robot-only FK. No new weights are trained here.
"""
from __future__ import annotations
from pathlib import Path
import time
from uuid import uuid4
import numpy as np
from PIL import Image
from ..contracts import Observation, ActionChunk
from ..controllers.ports import Proposal
from ..errors import InputRejected, ProtocolError
from ..transport import LocalClient, encode_observation, decode_observation
from ..trace import sha256_file

PANDA_JOINTS = tuple(f"panda_joint{i}" for i in range(1,8))


def droid_arrays(obs: Observation, camera_map: dict[str, str]) -> dict:
    if obs.robot != "franka" or obs.joint_names != PANDA_JOINTS:
        raise InputRejected("DROID adapter requires the verified Franka Panda 7-joint order")
    if set(camera_map) != {"wrist", "left", "right"} or len(set(camera_map.values())) != 3:
        raise InputRejected("DROID requires three distinct supplied cameras; no duplication/padding fallback")
    out = {"state": np.r_[obs.joints, 1.-obs.gripper_open].astype(np.float32)[None], "task": [obs.task]}
    for role, key in camera_map.items():
        if key not in obs.images: raise InputRejected(f"missing real camera role {key}")
        im = Image.fromarray(obs.images[key]).resize((640,360), Image.Resampling.BILINEAR)
        # uint8->float normalization on CPU, then move as a batch to the GPU.
        out["images."+role] = np.asarray(im).transpose(2,0,1).copy()[None].astype(np.float32)/255.
    return out


def droid_output_to_chunk(raw: np.ndarray, obs: Observation, model_identity: str) -> ActionChunk:
    a = np.asarray(raw)
    if a.ndim == 3 and a.shape[0] == 1: a = a[0]
    if a.ndim != 2 or a.shape[1] != 8 or not 1 <= len(a) <= 64 or not np.isfinite(a).all():
        raise InputRejected("FLUX DROID must return finite [1,H,8] or [H,8] absolute joint targets")
    a = a.astype(float).copy(); a[:, -1] = 1.-a[:, -1]
    # No silent clipping of model outliers, including gripper predictions.
    return ActionChunk("joint_absolute", a, obs.key, obs.control_dt,
                       "flux:"+model_identity, obs.joint_names, "flux_"+uuid4().hex)


class FluxEngine:
    def __init__(self, checkpoint: str | Path, camera_map: dict[str,str], device="cuda:0", compile_model=False,
                 gripper_boundary_tolerance=0.):
        if not np.isfinite(gripper_boundary_tolerance) or not 0 <= gripper_boundary_tolerance <= .01:
            raise ValueError("gripper boundary tolerance must be between 0 and 0.01")
        self.gripper_boundary_tolerance = gripper_boundary_tolerance
        path = Path(checkpoint).resolve()
        if not path.is_dir():
            raise ValueError("pass a local, explicitly downloaded FLUX package directory; no implicit Hub download")
        if not (path/"config.json").exists() and not (path/"config.native.json").exists():
            raise ValueError("checkpoint directory lacks config")
        from flux_action.policy import FluxActionPolicy
        import torch
        self.torch = torch; self.device = device; self.camera_map = camera_map
        self.policy = FluxActionPolicy.from_pretrained(str(path), device=device)
        self.policy.prepare_inference(compile=compile_model)
        self.identity = str(path)
        self.fingerprint = {p.name: sha256_file(p) for p in path.iterdir()
                            if p.is_file() and p.suffix in (".json",) }
        self.compile_model = compile_model

    def dispatch(self, path, payload):
        if path == "/metadata":
            return {"backend": "flux_action_droid", "checkpoint": self.identity, "config_hashes": self.fingerprint,
                    "camera_map": self.camera_map, "compile_model": self.compile_model,
                    "gripper_boundary_tolerance": self.gripper_boundary_tolerance,
                    "output": "32x(7 absolute joint radians + closed fraction)", "task_transfer_verified": False}
        if path != "/propose" or set(payload) != {"observation"}:
            raise InputRejected("only /metadata and /propose are available")
        obs = decode_observation(payload["observation"])
        values = droid_arrays(obs, self.camera_map)
        torch = self.torch
        batch = {k: torch.from_numpy(v).to(self.device) if isinstance(v, np.ndarray) else v for k,v in values.items()}
        started = time.monotonic()
        with torch.no_grad():
            raw = self.policy.predict_action_chunk(batch)
        if str(self.device).startswith("cuda"): torch.cuda.synchronize(self.device)
        raw = raw.detach().float().cpu().numpy() if hasattr(raw, "detach") else np.asarray(raw)
        raw, conversion = gripper_boundary_conversion(raw, self.gripper_boundary_tolerance)
        action = droid_output_to_chunk(raw, obs, Path(self.identity).name)
        return {"action": action.to_dict(), "identity": self.identity,
                "boundary_conversion": conversion,
                "inference_seconds": time.monotonic()-started, "config_hashes": self.fingerprint}


class RemoteFluxProposer:
    def __init__(self, client: LocalClient, env):
        self.client, self.env = client, env
        self.metadata = client.call("/metadata")
        self.qualification_acknowledged = False

    def propose(self, obs: Observation) -> Proposal:
        if not self.qualification_acknowledged:
            raise InputRejected("FLUX-to-EmbodiedSWE is experimental; pass --ack-experimental-flux after capture/FK qualification")
        obj = self.client.call("/propose", {"observation": encode_observation(obs)})
        action = ActionChunk.from_dict(obj["action"])
        if action.observation_id != obs.key: raise ProtocolError("stale FLUX proposal")
        fk = self.env.fk_preview(obs, action.values[:,:-1])
        if fk.shape != (len(action.values), 7): raise ProtocolError("FK shape mismatch")
        return Proposal(action, np.c_[fk, action.values[:,-1]], str(obj["identity"]), float(obj["inference_seconds"]),
                        obj.get("boundary_conversion"))

    def close(self):
        self.client.close()


def gripper_boundary_conversion(raw: np.ndarray, tolerance: float) -> tuple[np.ndarray, dict]:
    """Explicit proposal conversion only; canonical execution validation is unchanged."""
    if not np.isfinite(tolerance) or not 0 <= tolerance <= .01:
        raise InputRejected("gripper boundary tolerance must be between 0 and 0.01")
    a = np.asarray(raw)
    if a.ndim == 3 and a.shape[0] == 1:
        a = a[0]
    if a.ndim != 2 or a.shape[1] != 8 or not 1 <= len(a) <= 64 or not np.isfinite(a).all():
        raise InputRejected("invalid FLUX raw proposal")
    closed = a[:, -1]
    overshoot = np.maximum(np.maximum(-closed, closed - 1), 0)
    if np.any(overshoot > tolerance):
        raise InputRejected(f"FLUX gripper overshoot {float(overshoot.max()):.8f} exceeds declared tolerance {tolerance}")
    result = a.copy()
    result[:, -1] = np.clip(closed, 0, 1)
    return result, {"kind": "explicit_gripper_boundary_saturation", "tolerance": tolerance,
                    "raw_closed_fractions": closed.tolist(),
                    "converted_closed_fractions": result[:, -1].tolist(),
                    "changed_indices": np.flatnonzero(overshoot > 0).tolist(),
                    "max_overshoot": float(overshoot.max()), "joint_targets_modified": False}
