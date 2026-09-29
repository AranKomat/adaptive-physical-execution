"""Robot-state-only port of the frozen reference's approach/grasp OSC feedback.

Simulator pilot only: these gains and native action units are not hardware-safe
defaults. No object state, payload truth or scene-specific target is used here.
"""
import numpy as np
from .geometry import finite_vector, pose_error, unit_quaternion, quat_mul, rotvec_to_quat


class ReferenceOSC:
    def __init__(self):
        self.position_integral = np.zeros(3)
        self.rotation_integral = np.zeros(3)

    def command(self, measured_pose, target_pose, finger_position_m):
        if not np.isfinite(finger_position_m) or not 0 <= finger_position_m <= .04:
            raise ValueError("finger command must be per-finger meters in [0,.04]")
        target = finite_vector(target_pose, 7)
        target[3:] = unit_quaternion(target[3:])
        error = pose_error(measured_pose, target)
        self.position_integral = np.clip(self.position_integral + .035 * error[:3], -.16, .16)
        self.rotation_integral = np.clip(self.rotation_integral + .025 * error[3:], -1.5, 1.5)
        delta = np.r_[np.clip((error[:3] + self.position_integral) / .02, -5, 5),
                      np.clip((error[3:] + self.rotation_integral) / .097, -5, 5)]
        return np.r_[delta, finger_position_m, finger_position_m]


class NativeDiffIKFeedback:
    """Absolute-target feedback for upstream's relative-delta native controller."""
    def __init__(self, pos_scale, rot_scale, *, control_dt=1/48, integral_feedback=False):
        if not np.isfinite([pos_scale,rot_scale]).all() or min(pos_scale,rot_scale) <= 0:
            raise ValueError('invalid native action scales')
        self.pos_scale, self.rot_scale = pos_scale, rot_scale
        if not np.isfinite(control_dt) or not 0 < control_dt <= .1:
            raise ValueError('invalid feedback dt')
        self.control_dt, self.integral_feedback = control_dt, integral_feedback
        self.position_integral = np.zeros(3)

    def command(self, measured_pose, target_pose, finger_position_m):
        if not np.isfinite(finger_position_m) or not 0 <= finger_position_m <= .04:
            raise ValueError('invalid per-finger command')
        error = pose_error(measured_pose, target_pose)
        if self.integral_feedback:
            # Same time-normalized position integral gain as the reference OSC,
            # bounded to 3 cm; no mass, COM or hidden grasp-state feedforward.
            self.position_integral = np.clip(self.position_integral + .525*self.control_dt*error[:3],-.03,.03)
            error[:3] += self.position_integral
        translation_cap = .03 if self.integral_feedback else .01
        error[:3] *= min(1., translation_cap/max(np.linalg.norm(error[:3]),1e-12))
        error[3:] *= min(1., .05/max(np.linalg.norm(error[3:]),1e-12))
        return np.r_[error[:3]/self.pos_scale,error[3:]/self.rot_scale,
                     finger_position_m,finger_position_m]


def phases_at_cadence(value, control_dt):
    reference_dt = value.get('reference_control_dt',1/15)
    if not np.isfinite([reference_dt,control_dt]).all() or not 0 < min(reference_dt,control_dt):
        raise ValueError('invalid cadence')
    # Validate original counts before conversion, never turn fractional/negative
    # user actions into valid integers by rounding them.
    validate_plan(value,value.get('observation_id'),10**6)
    return [{**p,'actions':max(1,round(p['actions']*reference_dt/control_dt))}
            for p in value['phases']]


def ramped_target(start_pose, target_pose, step, translation_per_action=.0015):
    start = finite_vector(start_pose, 7)
    target = finite_vector(target_pose, 7)
    if type(step) is not int or step < 1 or not 0 < translation_per_action <= .003:
        raise ValueError('invalid ramp step')
    if np.linalg.norm(pose_error(start, target)[3:]) > .15:
        raise ValueError('translation-only ramp requires approximately fixed orientation')
    delta = target[:3]-start[:3]
    result = target.copy()
    result[:3] = start[:3] + delta * min(1., step*translation_per_action/max(np.linalg.norm(delta),1e-12))
    return result


def ramped_pose_target(start_pose, target_pose, step, translation_per_action, rotation_per_action):
    """Rate-limit translation and shortest-path world rotation independently."""
    start = finite_vector(start_pose, 7)
    target = finite_vector(target_pose, 7)
    if (type(step) is not int or step < 1
            or not 0 < translation_per_action <= .003
            or not 0 < rotation_per_action <= .01):
        raise ValueError('invalid pose ramp step or rates')
    error = pose_error(start, target)
    position_fraction = min(1., step*translation_per_action/max(np.linalg.norm(error[:3]), 1e-12))
    rotation_fraction = min(1., step*rotation_per_action/max(np.linalg.norm(error[3:]), 1e-12))
    return np.r_[start[:3]+error[:3]*position_fraction,
                 quat_mul(rotvec_to_quat(error[3:]*rotation_fraction), unit_quaternion(start[3:]))]


def motion_stop_reason(measured_pose, target_pose, arm_joints, arm_limits):
    if np.linalg.norm(pose_error(measured_pose, target_pose)[3:]) > .35:
        return 'orientation departed by more than 0.35 rad'
    q = finite_vector(arm_joints, 7)
    limits = np.asarray(arm_limits)
    if limits.shape != (7,2) or not np.isfinite(limits).all():
        raise ValueError('invalid robot-only joint limits')
    if np.any(q <= limits[:,0]+.005) or np.any(q >= limits[:,1]-.005):
        return 'arm within 0.005 rad of joint limit'
    return None


def validate_plan(value, observation_id, actions_remaining, max_phase_actions=180):
    if value.get("observation_id") != observation_id:
        raise ValueError("stale or unrelated observation")
    phases = value.get("phases")
    if not isinstance(phases, list) or not 0 <= len(phases) <= 4:
        raise ValueError("expected one to four bounded phases")
    if not phases and value.get('finish') is not True:
        raise ValueError('empty plan must explicitly finish without motion')
    total = 0
    for phase in phases:
        pose = finite_vector(phase["hand_pose_world"], 7)
        unit_quaternion(pose[3:])
        # Broad robot workcell bound, not obstacle clearance certification.
        if np.any(pose[:3] < [-.1, -.8, .12]) or np.any(pose[:3] > [.9, .6, .8]):
            raise ValueError("target outside pilot workcell")
        n = phase["actions"]
        if type(n) is not int or not 1 <= n <= max_phase_actions:
            raise ValueError("phase action cap invalid")
        grip = phase["finger_position_m"]
        if not isinstance(grip, (int, float)) or not np.isfinite(grip) or not 0 <= grip <= .04:
            raise ValueError("invalid per-finger command")
        if not isinstance(phase["name"], str) or not phase["name"]:
            raise ValueError("phase needs a label")
        total += n
    if total > actions_remaining:
        raise ValueError("episode action budget exceeded")
    if type(value.get("finish")) is not bool:
        raise ValueError("explicit finish boolean required")
    return phases
