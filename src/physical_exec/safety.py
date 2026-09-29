"""Simulation command validation, NOT a certified robot safety system."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .contracts import ActionChunk, Observation
from .errors import InputRejected
from .geometry import integrate_world_deltas, pose_error


@dataclass(frozen=True)
class Limits:
    max_translation_m: float = .03
    max_rotation_rad: float = .15
    max_joint_step_rad: float = .15
    max_chunk: int = 32
    workspace_low: tuple[float, float, float] = (-2, -2, -1)
    workspace_high: tuple[float, float, float] = (2, 2, 3)

    def __post_init__(self):
        for v in (self.max_translation_m, self.max_rotation_rad, self.max_joint_step_rad):
            if not np.isfinite(v) or v <= 0:
                raise ValueError("limits must be positive finite values")
        if type(self.max_chunk) is not int or not 1 <= self.max_chunk <= 64:
            raise ValueError("max_chunk must be 1..64")
        if np.shape(self.workspace_low) != (3,) or np.shape(self.workspace_high) != (3,):
            raise ValueError("workspace requires two 3-vectors")
        if not np.isfinite([*self.workspace_low, *self.workspace_high]).all() or np.any(np.asarray(self.workspace_low) >= self.workspace_high):
            raise ValueError("invalid workspace")


def validate_chunk(action: ActionChunk, observation: Observation, limits: Limits,
                   joint_limits: np.ndarray | None = None) -> ActionChunk:
    """Reject stale/out-of-bounds actions before execution; never silently clip."""
    if action.observation_id != observation.key:
        raise InputRejected("stale action: observation id differs")
    if not np.isclose(action.control_dt, observation.control_dt, rtol=0, atol=1e-8):
        raise InputRejected("action/control period mismatch; do not silently resample")
    if len(action.values) > limits.max_chunk:
        raise InputRejected("action horizon exceeds configured limit")
    a = action.values
    if action.kind == "joint_absolute":
        if action.joint_names != observation.joint_names:
            raise InputRejected("joint order mismatch")
        delta = np.diff(np.vstack([observation.joints, a[:, :-1]]), axis=0)
        if np.max(np.abs(delta)) > limits.max_joint_step_rad + 1e-9:
            raise InputRejected("successive joint target step exceeds limit")
        if joint_limits is not None:
            lim = np.asarray(joint_limits)
            if lim.shape != (len(observation.joints), 2):
                raise ValueError("invalid joint limits")
            if np.any(a[:, :-1] < lim[:, 0]) or np.any(a[:, :-1] > lim[:, 1]):
                raise InputRejected("joint target exceeds URDF limits")
        return action
    if action.kind == "eef_delta_world":
        if np.any(np.linalg.norm(a[:, :3], axis=1) > limits.max_translation_m + 1e-9):
            raise InputRejected("translation exceeds Euclidean, not per-axis, bound")
        if np.any(np.linalg.norm(a[:, 3:6], axis=1) > limits.max_rotation_rad + 1e-9):
            raise InputRejected("world rotation increment exceeds bound")
        absolute = integrate_world_deltas(observation.eef_pose, a)
    else:
        absolute = a
    previous = observation.eef_pose
    for row in absolute:
        e = pose_error(previous, row[:7])
        if np.linalg.norm(e[:3]) > limits.max_translation_m + 1e-9:
            raise InputRejected("successive EEF translation exceeds bound")
        if np.linalg.norm(e[3:]) > limits.max_rotation_rad + 1e-9:
            raise InputRejected("successive EEF rotation exceeds bound")
        if np.any(row[:3] < limits.workspace_low) or np.any(row[:3] > limits.workspace_high):
            raise InputRejected("target outside configured simulation workspace")
        previous = row[:7]
    return ActionChunk("eef_absolute_world", absolute, action.observation_id,
                       action.control_dt, action.source, proposal_id=action.proposal_id)
