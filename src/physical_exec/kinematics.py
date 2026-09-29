"""Robot-only URDF FK/Jacobian/DLS IK, with no simulator object access.

This is a reference, position-tracking controller. It is not a collision planner,
force controller, or a substitute for a validated real-robot controller.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .geometry import (finite_vector, rpy_matrix, quat_to_matrix, rotvec_to_quat,
                       matrix_pose, pose_matrix, pose_error)


@dataclass(frozen=True)
class Joint:
    name: str
    parent: str
    child: str
    kind: str
    origin: np.ndarray
    axis: np.ndarray
    lower: float
    upper: float


@dataclass(frozen=True)
class IKResult:
    joints: np.ndarray
    converged: bool
    position_error_m: float
    rotation_error_rad: float
    iterations: int


class URDFKinematics:
    def __init__(self, joints: list[Joint], root: str, tip: str):
        by_child = {j.child: j for j in joints}
        if len(by_child) != len(joints):
            raise ValueError("URDF has duplicate child links")
        chain, seen, cursor = [], set(), tip
        while cursor != root:
            if cursor in seen or cursor not in by_child:
                raise ValueError(f"no acyclic URDF chain from {root} to {tip}")
            seen.add(cursor)
            j = by_child[cursor]; chain.append(j); cursor = j.parent
        self.chain = list(reversed(chain))
        self.root, self.tip = root, tip
        self.active = [j for j in self.chain if j.kind != "fixed"]
        self.joint_names = tuple(j.name for j in self.active)
        self.limits = np.array([[j.lower, j.upper] for j in self.active], dtype=float)
        if not self.active:
            raise ValueError("chain has no actuated joints")

    @classmethod
    def from_urdf(cls, path: str | Path, root: str = "panda_link0", tip: str = "panda_hand"):
        p = Path(path)
        raw = p.read_bytes()
        if len(raw) > 10_000_000 or b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
            raise ValueError("unsupported URDF size or XML entities")
        tree = ET.fromstring(raw)
        joints = []
        for e in tree.findall("joint"):
            kind = e.attrib["type"]
            # Irrelevant finger branches may contain mimic tags. Reject only on selected chain.
            if e.find("mimic") is not None:
                kind = "mimic"
            origin = np.eye(4)
            o = e.find("origin")
            if o is not None:
                origin[:3, 3] = finite_vector([float(x) for x in o.get("xyz", "0 0 0").split()], 3)
                origin[:3, :3] = rpy_matrix([float(x) for x in o.get("rpy", "0 0 0").split()])
            a = e.find("axis")
            axis = finite_vector([float(x) for x in (a.get("xyz", "1 0 0") if a is not None else "1 0 0").split()], 3)
            if np.linalg.norm(axis) < 1e-10:
                raise ValueError("zero joint axis")
            axis /= np.linalg.norm(axis)
            lim = e.find("limit")
            lo, hi = (-np.pi, np.pi)
            if kind == "fixed":
                lo, hi = 0., 0.
            elif kind != "continuous":
                if lim is not None:
                    lo, hi = float(lim.get("lower", "-3.141592653589793")), float(lim.get("upper", "3.141592653589793"))
            joints.append(Joint(e.attrib["name"], e.find("parent").attrib["link"],
                                e.find("child").attrib["link"], kind, origin, axis, lo, hi))
        obj = cls(joints, root, tip)
        if any(j.kind not in {"fixed", "revolute", "prismatic", "continuous"} for j in obj.chain):
            raise ValueError("selected chain includes unsupported joint type/mimic")
        return obj

    def _walk(self, q, base_pose=None):
        q = finite_vector(q, len(self.active), "joint configuration")
        t = np.eye(4) if base_pose is None else pose_matrix(base_pose)
        frames = []
        i = 0
        for j in self.chain:
            t = t @ j.origin
            if j.kind == "fixed":
                continue
            frames.append((j.kind, t[:3, 3].copy(), t[:3, :3] @ j.axis))
            m = np.eye(4)
            if j.kind in ("revolute", "continuous"):
                m[:3, :3] = quat_to_matrix(rotvec_to_quat(j.axis*q[i]))
            elif j.kind == "prismatic":
                m[:3, 3] = j.axis*q[i]
            t = t @ m; i += 1
        return t, frames

    def fk(self, q, base_pose=None) -> np.ndarray:
        return matrix_pose(self._walk(q, base_pose)[0])

    def jacobian(self, q, base_pose=None) -> np.ndarray:
        t, frames = self._walk(q, base_pose)
        j = np.zeros((6, len(frames)))
        for i, (kind, position, axis) in enumerate(frames):
            if kind == "prismatic":
                j[:3, i] = axis
            else:
                j[:3, i] = np.cross(axis, t[:3, 3]-position)
                j[3:, i] = axis
        return j

    def solve(self, target, seed, base_pose=None, *, iterations=80, damping=.02,
              max_iteration_step=.08, position_tolerance=.002, rotation_tolerance=.02) -> IKResult:
        q = finite_vector(seed, len(self.active), "IK seed")
        target = finite_vector(target, 7, "target pose")
        pose_matrix(target)  # validate quaternion
        if iterations < 1 or damping <= 0 or max_iteration_step <= 0:
            raise ValueError("invalid IK solver configuration")
        for step in range(iterations):
            e = pose_error(self.fk(q, base_pose), target)
            pe, re = float(np.linalg.norm(e[:3])), float(np.linalg.norm(e[3:]))
            if pe <= position_tolerance and re <= rotation_tolerance:
                return IKResult(q, True, pe, re, step)
            j = self.jacobian(q, base_pose)
            dq = j.T @ np.linalg.solve(j @ j.T + damping*damping*np.eye(6), e)
            # Per-iteration limiting is solver numerics, not silent execution clipping.
            dq *= min(1., max_iteration_step / max(float(np.max(np.abs(dq))), 1e-12))
            q = np.clip(q+dq, self.limits[:, 0], self.limits[:, 1])
        e = pose_error(self.fk(q, base_pose), target)
        pe, re = float(np.linalg.norm(e[:3])), float(np.linalg.norm(e[3:]))
        return IKResult(q, pe <= position_tolerance and re <= rotation_tolerance, pe, re, iterations)
