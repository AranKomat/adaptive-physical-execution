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


def surface_patch(depth, calibration, pixel, *, radius=1, max_spread_m=.01):
    """Fit a visible local plane; its normal does not establish object identity."""
    if type(radius) is not int or not 1 <= radius <= 3:
        raise ValueError('Plane fit requires radius1..3')
    measurement = surface_point(depth, calibration, pixel, radius=radius, max_spread_m=max_spread_m)
    u, v = measurement['pixel_uv']
    points = np.array([surface_point(depth, calibration, [x, y], radius=0)['surface_point_world_m']
                       for y in range(v-radius, v+radius+1)
                       for x in range(u-radius, u+radius+1)])
    centered = points-points.mean(axis=0)
    _, singular, vectors = np.linalg.svd(centered, full_matrices=False)
    if singular[1] < 1e-5:
        raise ValueError('Insufficient two-dimensional patch extent')
    normal = vectors[-1]
    if normal[2] < 0:
        normal = -normal
    return dict(measurement, plane_normal_world_up_hemisphere=normal.tolist(),
                plane_rms_m=float(np.sqrt(np.mean((centered@normal)**2))),
                normal_up_cosine=float(normal[2]), plane_sample_count=len(points),
                normal_limitation='Observed local plane, sign chosen toward world up; not object identity, outward normal, contact or clearance')


def project_surface_memory(measurement, calibration, depth):
    """Project an earlier sensor sample; a depth match is not semantic identity."""
    old_episode, old_seq = measurement['observation_id'].rsplit(':',1)
    episode, seq = calibration['observation_id'].rsplit(':',1)
    if old_episode!=episode or int(old_seq)>=int(seq):
        raise ValueError('Memory must precede current observation in the same episode')
    if calibration['depth_convention']!='camera_optical_z' or calibration['depth_units']!='meters':
        raise ValueError('Unsupported depth convention')
    point = finite_vector(measurement['surface_point_world_m'],3)
    eye = finite_vector(calibration['camera_position_world'],3)
    local = quat_to_matrix(calibration['camera_quaternion_world_wxyz_optical']).T@(point-eye)
    k = np.asarray(calibration['intrinsic_matrix'],dtype=float)
    d = np.asarray(depth)
    if (d.ndim!=2 or k.shape!=(3,3) or not np.isfinite(k).all()
            or k[0,0]<=0 or k[1,1]<=0 or not np.allclose(k[2],[0,0,1])):
        raise ValueError('Invalid projection inputs')
    result = dict(source_observation_id=measurement['observation_id'],
        current_observation_id=calibration['observation_id'],
        limitation='Assumes historical surface static; depth agreement is not identity, free space or mating geometry.')
    if local[2]<=0:
        return dict(result,status='behind_camera')
    pixel = (k@local)[:2]/local[2]
    result.update(projected_pixel_uv=pixel.tolist(),predicted_optical_depth_m=float(local[2]))
    u,v = np.rint(pixel).astype(int)
    if not (0<=pixel[0]<d.shape[1] and 0<=pixel[1]<d.shape[0] and 0<=u<d.shape[1] and 0<=v<d.shape[0]):
        return dict(result,status='outside_image')
    actual = float(d[v,u])
    if not np.isfinite(actual) or actual<=0:
        return dict(result,status='invalid_current_depth')
    residual = actual-float(local[2])
    return dict(result,status='depth_consistent' if abs(residual)<=.01 else 'depth_inconsistent',
                sampled_pixel_uv=[int(u),int(v)],current_optical_depth_m=actual,
                depth_residual_m=residual,depth_comparison_tolerance_m=.01)
