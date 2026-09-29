"""Small explicit policy-facing contract; no arbitrary simulator metadata.

Single-arm first release. Canonical gripper is OPEN fraction (0 closed, 1 open).
FLUX and EvalSim use CLOSED fraction: adapters invert at that boundary only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping
import math
import numpy as np
from .geometry import finite_vector, unit_quaternion


def safe_text(value: Any, name: str, limit: int = 10000) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ValueError(f"{name} must be a nonempty string up to {limit} characters")
    return value


@dataclass(frozen=True)
class Observation:
    episode_id: str
    seq: int
    sim_time: float
    task: str
    robot: str
    images: Mapping[str, np.ndarray]
    joints: np.ndarray
    joint_names: tuple[str, ...]
    eef_pose: np.ndarray  # world xyz + wxyz, robot-derived (not object truth)
    gripper_open: float
    control_dt: float
    eef_frame: str = "panda_hand"

    def __post_init__(self):
        for n in ("episode_id", "task", "robot", "eef_frame"):
            safe_text(getattr(self, n), n)
        if type(self.seq) is not int or self.seq < 0:
            raise ValueError("seq must be a nonnegative integer")
        if not math.isfinite(self.sim_time) or self.sim_time < 0:
            raise ValueError("invalid sim time")
        if not math.isfinite(self.control_dt) or self.control_dt <= 0:
            raise ValueError("invalid control period")
        if not isinstance(self.gripper_open, (int, float)) or isinstance(self.gripper_open, bool) or not 0 <= self.gripper_open <= 1:
            raise ValueError("gripper_open must be a finite fraction")
        if not self.joint_names or len(set(self.joint_names)) != len(self.joint_names):
            raise ValueError("joint names must be nonempty and unique")
        joints = finite_vector(self.joints, len(self.joint_names), "joints")
        pose = finite_vector(self.eef_pose, 7, "eef pose")
        pose[3:] = unit_quaternion(pose[3:])
        if not self.images:
            raise ValueError("at least one camera is required")
        imgs = {}
        for role, value in self.images.items():
            safe_text(role, "camera role", 80)
            a = np.asarray(value)
            if a.dtype != np.uint8 or a.ndim != 3 or a.shape[-1] != 3 or min(a.shape[:2]) < 1:
                raise ValueError(f"{role}: expected uint8 HWC RGB, got {a.shape}/{a.dtype}")
            if max(a.shape[:2]) > 4096:
                raise ValueError("camera frame exceeds the 4096 pixel transport cap")
            a = a.copy(); a.flags.writeable = False; imgs[role] = a
        joints.flags.writeable = False; pose.flags.writeable = False
        object.__setattr__(self, "joints", joints)
        object.__setattr__(self, "eef_pose", pose)
        object.__setattr__(self, "images", imgs)

    @property
    def key(self) -> str:
        return f"{self.episode_id}:{self.seq}"

    def public_state(self) -> dict:
        """Allowlist serialization, never dataclasses.asdict(raw simulator result)."""
        return {"observation_id": self.key, "episode_id": self.episode_id,
                "step": self.seq, "sim_time_seconds": self.sim_time,
                "task": self.task, "robot": self.robot,
                "joints_rad": self.joints.tolist(), "joint_names": list(self.joint_names),
                "eef_pose_world_xyz_wxyz": self.eef_pose.tolist(), "eef_frame": self.eef_frame,
                "gripper_open_fraction": self.gripper_open,
                "gripper_state_source": "measured aperture; not grasp verification",
                "control_dt_seconds": self.control_dt,
                "camera_roles": list(self.images)}


@dataclass(frozen=True)
class ActionChunk:
    kind: Literal["eef_delta_world", "eef_absolute_world", "joint_absolute"]
    values: np.ndarray
    observation_id: str
    control_dt: float
    source: str
    joint_names: tuple[str, ...] = ()
    proposal_id: str | None = None

    def __post_init__(self):
        if self.kind not in ("eef_delta_world", "eef_absolute_world", "joint_absolute"):
            raise ValueError("unknown action kind")
        n = 7 if self.kind == "eef_delta_world" else 8 if self.kind == "eef_absolute_world" else len(self.joint_names) + 1
        if self.kind == "joint_absolute" and (not self.joint_names or len(set(self.joint_names)) != len(self.joint_names)):
            raise ValueError("joint command requires explicit unique joint order")
        a = np.asarray(self.values, dtype=np.float64)
        if a.ndim != 2 or a.shape[1] != n or not 1 <= len(a) <= 64 or not np.isfinite(a).all():
            raise ValueError(f"{self.kind}: expected 1..64 rows of {n} finite values")
        if np.any(a[:, -1] < 0) or np.any(a[:, -1] > 1):
            raise ValueError("canonical gripper uses open fraction in [0,1]")
        a = a.copy()
        if self.kind == "eef_absolute_world":
            for row in a:
                row[3:7] = unit_quaternion(row[3:7])
        if not math.isfinite(self.control_dt) or self.control_dt <= 0:
            raise ValueError("control_dt must be positive")
        safe_text(self.observation_id, "observation_id", 200)
        safe_text(self.source, "source", 200)
        a.flags.writeable = False
        object.__setattr__(self, "values", a)

    def prefix(self, n: int) -> "ActionChunk":
        if type(n) is not int or not 1 <= n <= len(self.values):
            raise ValueError("prefix outside chunk")
        return ActionChunk(self.kind, self.values[:n], self.observation_id, self.control_dt,
                           self.source, self.joint_names, self.proposal_id)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "values": self.values.tolist(),
                "observation_id": self.observation_id, "control_dt": self.control_dt,
                "source": self.source, "joint_names": list(self.joint_names),
                "proposal_id": self.proposal_id}

    @classmethod
    def from_dict(cls, obj: dict) -> "ActionChunk":
        keys = {"kind", "values", "observation_id", "control_dt", "source", "joint_names", "proposal_id"}
        if set(obj) - keys:
            raise ValueError(f"unknown action fields {set(obj)-keys}")
        return cls(**{**obj, "joint_names": tuple(obj.get("joint_names", ()))})


@dataclass(frozen=True)
class ExecutionReceipt:
    command_id: str
    observation_id: str
    resulting_observation_id: str
    requested_steps: int
    executed_steps: int
    status: Literal["executed", "rejected", "interrupted"]
    reason: str
    source: str
    sim_seconds: float
    wall_seconds: float
    tracking_position_error_m: float | None = None
    tracking_rotation_error_rad: float | None = None

    def __post_init__(self):
        for name in ("command_id", "observation_id", "resulting_observation_id", "source"):
            safe_text(getattr(self, name), name, 300)
        if any(type(n) is not int for n in (self.requested_steps, self.executed_steps)) or not 0 <= self.executed_steps <= self.requested_steps <= 64:
            raise ValueError("invalid receipt step counts")
        if self.status not in ("executed", "rejected", "interrupted"):
            raise ValueError("invalid receipt status")
        if self.status == "rejected" and self.executed_steps != 0:
            raise ValueError("rejected receipt cannot describe execution")
        for value in (self.sim_seconds, self.wall_seconds, self.tracking_position_error_m, self.tracking_rotation_error_rad):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError("invalid receipt measurement")

    def to_dict(self) -> dict:
        # Only controller facts, never object outcomes/privileged scorer results.
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass(frozen=True)
class Evaluation:
    """Host-only: never sent to a language model or memory serializer."""
    success: bool = False
    score: float | None = None
    native: bool = False
    note: str = "not evaluated"

    def __post_init__(self):
        if type(self.success) is not bool or type(self.native) is not bool:
            raise ValueError("evaluation flags must be booleans")
        if self.score is not None and (isinstance(self.score, bool) or not math.isfinite(self.score)):
            raise ValueError("evaluation score must be finite or absent")


@dataclass(frozen=True)
class StepResult:
    observation: Observation
    receipt: ExecutionReceipt
    evaluation: Evaluation = field(default_factory=Evaluation)


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0  # subset of output, do not add again
    latency_seconds: float = 0.0
    calls: int = 1
    usage_reported: bool = True

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @classmethod
    def from_response(cls, obj: dict, latency: float) -> "Usage":
        u = obj.get("usage") or {}
        return cls(input_tokens=int(u.get("input_tokens", 0)),
                   cached_input_tokens=int((u.get("input_tokens_details") or {}).get("cached_tokens", 0)),
                   output_tokens=int(u.get("output_tokens", 0)),
                   reasoning_tokens=int((u.get("output_tokens_details") or {}).get("reasoning_tokens", 0)),
                   latency_seconds=latency, usage_reported=bool(obj.get("usage")))
