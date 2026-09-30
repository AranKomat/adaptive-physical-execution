"""Offline rest-to-rest EEF transit candidates; not clearance or tracking qualification.

One quintic time law spans the whole straight transit, not each logging waypoint.
Velocity and acceleration vanish at both endpoints. Joint limits, payload and
obstacles still require independent checks before execution.
"""
import math

import numpy as np

from .geometry import finite_vector, pose_error, quat_mul, rotvec_to_quat, unit_quaternion


def transit_trajectory(start, target, *, speed_scale, dt=1/15,
                       linear_acceleration=.45, angular_acceleration=1.2):
    if speed_scale not in (5, 10) or isinstance(speed_scale, bool):
        raise ValueError('qualification scale must be 5 or 10')
    values = [dt, linear_acceleration, angular_acceleration]
    if not np.isfinite(values).all() or min(values) <= 0 or dt > 1/15+1e-10:
        raise ValueError('invalid cadence or acceleration limits')
    start, target = finite_vector(start, 7), finite_vector(target, 7)
    start[3:], target[3:] = unit_quaternion(start[3:]), unit_quaternion(target[3:])
    delta = pose_error(start, target)
    distance, angle = np.linalg.norm(delta[:3]), np.linalg.norm(delta[3:])
    linear_speed, angular_speed = .0225*speed_scale, .06*speed_scale
    # Exact maxima of derivatives of 10u^3 - 15u^4 + 6u^5.
    peak_velocity, peak_acceleration = 1.875, 10/math.sqrt(3)
    duration = max(dt, peak_velocity*distance/linear_speed,
                   peak_velocity*angle/angular_speed,
                   math.sqrt(peak_acceleration*distance/linear_acceleration),
                   math.sqrt(peak_acceleration*angle/angular_acceleration))
    steps = math.ceil(duration/dt)
    if steps > 4096:
        raise ValueError('offline trajectory exceeds sample cap')
    duration = steps*dt
    u = np.arange(steps+1)/steps
    s = 10*u**3 - 15*u**4 + 6*u**5
    poses = np.array([np.r_[start[:3]+fraction*delta[:3],
        quat_mul(rotvec_to_quat(fraction*delta[3:]), start[3:])] for fraction in s])
    return dict(poses=poses, duration_seconds=duration, steps=steps,
        linear_speed_limit_m_s=linear_speed, angular_speed_limit_rad_s=angular_speed,
        peak_linear_speed_m_s=float(peak_velocity*distance/duration),
        peak_angular_speed_rad_s=float(peak_velocity*angle/duration),
        peak_linear_acceleration_m_s2=float(peak_acceleration*distance/duration**2),
        peak_angular_acceleration_rad_s2=float(peak_acceleration*angle/duration**2),
        qualification='offline only; no motion, clearance or payload certification')
