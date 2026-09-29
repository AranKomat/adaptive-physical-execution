"""Sensor-derived surface measurements, never semantic object poses."""
import numpy as np
from .geometry import finite_vector, quat_to_matrix


def surface_point(depth, calibration, pixel, *, radius=2, max_spread_m=.02):
    """Reject invalid/mixed neighborhoods; report a surface point, not a grasp."""
    d = np.asarray(depth)
    if d.ndim != 2 or type(radius) is not int or not 0 <= radius <= 10:
        raise ValueError("expected depth image and bounded integer radius")
    if not np.isfinite(max_spread_m) or max_spread_m <= 0:
        raise ValueError("invalid spread threshold")
    uv = finite_vector(pixel, 2, "pixel")
    if not np.equal(uv, np.floor(uv)).all():
        raise ValueError("pixel must use integer original-image coordinates")
    u, v = uv.astype(int)
    if not radius <= u < d.shape[1]-radius or not radius <= v < d.shape[0]-radius:
        raise ValueError("pixel neighborhood exceeds image")
    patch = d[v-radius:v+radius+1, u-radius:u+radius+1]
    if not np.isfinite(patch).all() or np.any(patch <= 0):
        raise ValueError("invalid depth in selected neighborhood")
    spread = float(np.ptp(patch))
    if spread > max_spread_m:
        raise ValueError("depth discontinuity: select an interior surface pixel")
    if calibration["depth_convention"] != "camera_optical_z" or calibration["depth_units"] != "meters":
        raise ValueError("unsupported depth convention")
    k = np.asarray(calibration["intrinsic_matrix"], dtype=float)
    if k.shape != (3, 3) or not np.isfinite(k).all() or k[0,0] <= 0 or k[1,1] <= 0:
        raise ValueError("invalid camera intrinsics")
    if not np.allclose(k[2], [0, 0, 1]):
        raise ValueError("invalid pinhole intrinsics")
    z = float(d[v, u])
    camera_point = np.linalg.solve(k, [u, v, 1.]) * z
    world = (quat_to_matrix(calibration["camera_quaternion_world_wxyz_optical"]) @ camera_point
             + finite_vector(calibration["camera_position_world"], 3))
    return {"observation_id": calibration["observation_id"], "pixel_uv": [int(u), int(v)],
            "surface_point_world_m": world.tolist(), "optical_depth_m": z,
            "local_depth_spread_m": spread, "neighborhood_radius_pixels": radius,
            "limitation": "Visible surface only; spread is not calibrated uncertainty, identity or grasp pose."}
