"""Bounded idealized sensor positioning, not a physical rig or clearance proof."""
import numpy as np

from .geometry import finite_vector, pose_error


def camera_path(start_eye, end_eye, measured_hand, commanded_hand, actions, control_dt):
    start, end = finite_vector(start_eye, 3), finite_vector(end_eye, 3)
    low, high = np.array([0., -.7, .85]), np.array([1., .7, 1.6])
    if np.any(np.minimum(start, end) < low) or np.any(np.maximum(start, end) > high):
        raise ValueError('camera path outside declared overhead envelope')
    error = pose_error(measured_hand, commanded_hand)
    if np.linalg.norm(error[:3]) > .003 or np.linalg.norm(error[3:]) > .03:
        raise ValueError('camera inspection requires a hold target, not arm transit')
    if type(actions) is not int or actions < 1 or not np.isfinite(control_dt) or control_dt <= 0:
        raise ValueError('invalid camera movement duration')
    distance = np.linalg.norm(end-start)
    if distance > .65 or distance/(actions*control_dt) > .12 + 1e-10:
        raise ValueError('camera displacement or speed budget exceeded')
    return start + np.arange(1, actions+1)[:, None]/actions*(end-start)
