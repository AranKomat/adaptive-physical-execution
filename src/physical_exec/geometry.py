"""CPU robot geometry. SI units, right-handed world frame, quaternions wxyz.

Delta rotations are WORLD increments (left multiplication), as in RoboICL.
These functions do not inspect scene objects or advance a simulator.
"""
from __future__ import annotations
import math
import numpy as np
from numpy.typing import ArrayLike, NDArray


def finite_vector(value: ArrayLike, n: int, name: str = "vector") -> NDArray:
    a = np.asarray(value, dtype=np.float64)
    if a.shape != (n,) or not np.isfinite(a).all():
        raise ValueError(f"{name} must contain exactly {n} finite numbers")
    return a.copy()


def unit_quaternion(q: ArrayLike, tolerance: float = .05) -> NDArray:
    q = finite_vector(q, 4, "quaternion wxyz")
    norm = float(np.linalg.norm(q))
    if norm < 1e-8 or abs(norm - 1) > tolerance:
        raise ValueError("quaternion must be near unit length; no zero-quaternion fallback")
    return q / norm


def quat_mul(a: ArrayLike, b: ArrayLike) -> NDArray:
    w, x, y, z = np.asarray(a, dtype=float)
    v, i, j, k = np.asarray(b, dtype=float)
    return np.array([w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
                     w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v])


def quat_conj(q: ArrayLike) -> NDArray:
    q = np.asarray(q, dtype=float).copy()
    q[1:] *= -1
    return q


def rotvec_to_quat(v: ArrayLike) -> NDArray:
    v = finite_vector(v, 3, "rotation vector")
    a = float(np.linalg.norm(v))
    return np.r_[math.cos(a/2), v*(math.sin(a/2)/a if a > 1e-10 else .5)]


def quat_to_rotvec(q: ArrayLike) -> NDArray:
    q = unit_quaternion(q)
    if q[0] < 0:
        q = -q  # shortest rotation; q and -q encode the same pose
    s = float(np.linalg.norm(q[1:]))
    return 2*q[1:] if s < 1e-10 else q[1:] * (2*math.atan2(s, q[0])/s)


def quat_to_matrix(q: ArrayLike) -> NDArray:
    w, x, y, z = unit_quaternion(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def matrix_to_quat(r: ArrayLike) -> NDArray:
    r = np.asarray(r, dtype=float)
    if r.shape != (3, 3) or not np.isfinite(r).all():
        raise ValueError("rotation must be finite 3x3")
    if not np.allclose(r.T @ r, np.eye(3), atol=1e-6) or np.linalg.det(r) < .999:
        raise ValueError("rotation matrix is not in SO(3)")
    # Branch by largest diagonal component for numerical stability at pi.
    tr = float(np.trace(r))
    if tr > 0:
        s = math.sqrt(tr+1)*2
        q = [s/4, (r[2,1]-r[1,2])/s, (r[0,2]-r[2,0])/s, (r[1,0]-r[0,1])/s]
    else:
        i = int(np.argmax(np.diag(r)))
        if i == 0:
            s = math.sqrt(1+r[0,0]-r[1,1]-r[2,2])*2
            q = [(r[2,1]-r[1,2])/s, s/4, (r[0,1]+r[1,0])/s, (r[0,2]+r[2,0])/s]
        elif i == 1:
            s = math.sqrt(1+r[1,1]-r[0,0]-r[2,2])*2
            q = [(r[0,2]-r[2,0])/s, (r[0,1]+r[1,0])/s, s/4, (r[1,2]+r[2,1])/s]
        else:
            s = math.sqrt(1+r[2,2]-r[0,0]-r[1,1])*2
            q = [(r[1,0]-r[0,1])/s, (r[0,2]+r[2,0])/s, (r[1,2]+r[2,1])/s, s/4]
    return unit_quaternion(q)


def pose_matrix(pose: ArrayLike) -> NDArray:
    p = finite_vector(pose, 7, "pose xyz+wxyz")
    t = np.eye(4)
    t[:3, :3] = quat_to_matrix(p[3:])
    t[:3, 3] = p[:3]
    return t


def matrix_pose(t: ArrayLike) -> NDArray:
    t = np.asarray(t, dtype=float)
    if t.shape != (4, 4) or not np.allclose(t[3], [0, 0, 0, 1]):
        raise ValueError("expected homogeneous 4x4 transform")
    return np.r_[t[:3, 3], matrix_to_quat(t[:3, :3])]


def integrate_world_deltas(pose: ArrayLike, rows: ArrayLike) -> NDArray:
    """Rows [dx,dy,dz,rx,ry,rz,opening] -> [x,y,z,qw,qx,qy,qz,opening].

    Each row is relative to the PREVIOUS commanded target, not the start anchor.
    This distinction matters for accumulating rotations and action chunks.
    """
    pose = finite_vector(pose, 7, "pose")
    pose[3:] = unit_quaternion(pose[3:])
    rows = np.asarray(rows, dtype=float)
    if rows.ndim != 2 or rows.shape[1] != 7 or not np.isfinite(rows).all():
        raise ValueError("delta chunk must be Hx7 finite values")
    result = []
    for row in rows:
        pose = np.r_[pose[:3] + row[:3],
                     unit_quaternion(quat_mul(rotvec_to_quat(row[3:6]), pose[3:]))]
        result.append(np.r_[pose, row[-1]])
    return np.asarray(result).reshape(-1, 8)


def pose_error(current: ArrayLike, target: ArrayLike) -> NDArray:
    c, t = finite_vector(current, 7), finite_vector(target, 7)
    return np.r_[t[:3] - c[:3], quat_to_rotvec(quat_mul(t[3:], quat_conj(c[3:])))]


def rpy_matrix(rpy: ArrayLike) -> NDArray:
    r, p, y = finite_vector(rpy, 3)
    return quat_to_matrix(quat_mul(quat_mul(rotvec_to_quat([0, 0, y]),
                                            rotvec_to_quat([0, p, 0])),
                                   rotvec_to_quat([r, 0, 0])))
