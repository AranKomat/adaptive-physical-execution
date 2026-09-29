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


def standoff_stages(measurements, observation_id, hand_pose, opening, *, near=False):
    """Exploratory approach with 12/6 cm nominal separation, not a clearance bound."""
    if measurements.get('observation_id') != observation_id:
        raise ValueError('Standoff measurements are stale')
    hand = finite_vector(hand_pose,7)
    if isinstance(opening,bool) or not isinstance(opening,(float,int)) or not 0 <= opening <= 1:
        raise ValueError('Established gripper command required')
    points = {}
    for name, minimum in (('connector',2),('socket',1)):
        accepted = [s['measurement'] for s in measurements[name]['samples'] if 'measurement' in s]
        if len(accepted)<minimum or any(m['observation_id']!=observation_id for m in accepted):
            raise ValueError('Insufficient current feature measurements')
        if any(not np.isfinite(m['local_depth_spread_m']) or not 0 <= m['local_depth_spread_m'] <= .01
               or m['neighborhood_radius_pixels']!=1 for m in accepted):
            raise ValueError('Unsupported feature depth qualification')
        points[name] = np.array([finite_vector(m['surface_point_world_m'],3) for m in accepted])
    if np.max(np.linalg.norm(points['connector']-hand[:3],axis=1))>.35:
        raise ValueError('Connector samples too far from held hand')
    if near:
        pairs = []
        for end in ('end_a','end_b'):
            matched = []
            for name in ('connector','socket'):
                candidates = [s['measurement']['surface_point_world_m'] for s in measurements[name]['samples']
                              if 'measurement' in s and s.get('correspondence_end')==end]
                if len(candidates)==1:
                    matched.append(np.asarray(candidates[0]))
            if len(matched)==2:
                pairs.append(np.linalg.norm((matched[0]-matched[1])[:2]))
        if not pairs or max(pairs)>.01:
            raise ValueError('Near approach requires a measured corresponding end within 10mm horizontally')
    gap = float(np.min(points['connector'][:,2])-np.max(points['socket'][:,2]))
    floor, cap = (.06,.06) if near else (.12,.10)
    descent = min(cap,gap-floor)
    if not np.isfinite(descent) or descent<.01:
        raise ValueError('Insufficient measured standoff for this coarse approach')
    count = math.ceil(descent/.05)
    stages = []
    for i in range(1,count+1):
        pose = hand.copy()
        pose[2] -= descent*i/count
        stages.append(dict(hand_pose_world=pose.tolist(),gripper_open=opening,max_steps=64,
            settle_at_end=i==count,target_source='Operator-scoped measured-feature standoff; '
            f'>={floor*100:g}cm nominal vertical feature separation; unknown swept clearance; NOT insertion approval'))
    return stages
