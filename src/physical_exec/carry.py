"""Compile an elevated carry into bounded local stages, never insertion/release."""
import math

import numpy as np

from .geometry import finite_vector, pose_error


def carry_stages(plan, observation_id, hand_pose, opening):
    if plan.get('observation_id') != observation_id or plan.get('finish') is not False:
        raise ValueError('Carry requires a current, unfinished plan')
    if not isinstance(plan.get('target_source'), str) or not plan['target_source']:
        raise ValueError('Carry target provenance required')
    if not isinstance(opening, (float, int)) or not np.isfinite(opening):
        raise ValueError('Established gripper command required')
    phases = plan.get('phases')
    if not isinstance(phases, list) or not 1 <= len(phases) <= 4:
        raise ValueError('Invalid carry phases')
    start = finite_vector(hand_pose, 7).copy()
    origin = start.copy()
    stages = []
    total = 0.
    for phase in phases:
        if not phase.get('name', '').startswith('elevated_carry_'):
            raise ValueError('Only elevated carry is supported')
        finger = phase.get('finger_position_m')
        if finger is None or not np.isfinite(finger) or abs(finger-.04*opening) > 1e-8:
            raise ValueError('Carry must preserve gripper command')
        target = finite_vector(phase['hand_pose_world'], 7)
        error = pose_error(start, target)
        if (target[2] < start[2]-1e-8 or np.linalg.norm(pose_error(origin, target)[3:]) > .03
                or np.linalg.norm(target[:3]-origin[:3]) > .5):
            raise ValueError('Carry cannot descend, reorient, or exceed 0.5 m')
        distance = np.linalg.norm(error[:3])
        total += distance
        count = max(1, math.ceil(distance/.06))
        for i in range(1, count+1):
            pose = np.r_[start[:3]+(target[:3]-start[:3])*i/count, target[3:]]
            stages.append(dict(hand_pose_world=pose.tolist(), gripper_open=opening,
                               max_steps=64, settle_at_end=False,
                               target_source=plan['target_source']+'; elevated carry; unknown clearance'))
        start = target
    if total > .5 or len(stages) > 12:
        raise ValueError('Carry path budget exceeded')
    stages[-1]['settle_at_end'] = True
    return stages
