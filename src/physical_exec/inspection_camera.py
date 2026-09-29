"""Bounded idealized sensor positioning, not a physical rig or clearance proof."""
import numpy as np

from .geometry import finite_vector, pose_error


def camera_path(start_eye, end_eye, measured_hand, commanded_hand, actions, control_dt,
                *, oblique_envelope=False):
    start, end = finite_vector(start_eye, 3), finite_vector(end_eye, 3)
    low, high = np.array([0., -.7, .3 if oblique_envelope else .85]), np.array([1., .7, 1.6])
    if np.any(np.minimum(start, end) < low) or np.any(np.maximum(start, end) > high):
        raise ValueError('camera path outside declared inspection envelope')
    error = pose_error(measured_hand, commanded_hand)
    if np.linalg.norm(error[:3]) > .003 or np.linalg.norm(error[3:]) > .03:
        raise ValueError('camera inspection requires a hold target, not arm transit')
    if type(actions) is not int or actions < 1 or not np.isfinite(control_dt) or control_dt <= 0:
        raise ValueError('invalid camera movement duration')
    distance = np.linalg.norm(end-start)
    if distance > .65 or distance/(actions*control_dt) > .12 + 1e-10:
        raise ValueError('camera displacement or speed budget exceeded')
    return start + np.arange(1, actions+1)[:, None]/actions*(end-start)


def camera_gaze_path(start_eye, eye_path, start_gaze, end_gaze, control_dt):
    """Bound view direction changes as well as translation; avoid look-at singularities."""
    start, end = finite_vector(start_gaze, 3), finite_vector(end_gaze, 3)
    eyes = np.vstack([finite_vector(start_eye, 3), eye_path])
    gazes = start + np.linspace(0., 1., len(eyes))[:, None]*(end-start)
    directions = gazes-eyes
    distances = np.linalg.norm(directions, axis=1)
    if np.any(distances < .1):
        raise ValueError('camera eye too close to gaze target')
    directions /= distances[:, None]
    if np.any(np.linalg.norm(directions[:, :2], axis=1) < .01):
        raise ValueError('camera look-at direction too close to vertical singularity')
    angles = np.arccos(np.clip(np.sum(directions[1:]*directions[:-1], axis=1), -1., 1.))
    if np.max(angles)/control_dt > .35 + 1e-8:
        raise ValueError('camera angular speed budget exceeded')
    return gazes[1:]
