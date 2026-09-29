#!/usr/bin/env python3
"""Prepare a sensor-history-based closer-look proposal; never execute it."""
import argparse
import base64
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import pose_matrix, finite_vector
from physical_exec.osc_reference import validate_plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--source-capture', type=Path, required=True)
    p.add_argument('--carry-command', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--descent-m', type=float, default=.08)
    p.add_argument('--minimum-gap-m', type=float, default=.12)
    p.add_argument('--fresh-feature', type=Path)
    args = p.parse_args()
    if not 0 < args.descent_m <= .10 or not .05 <= args.minimum_gap_m <= .20:
        raise ValueError('invalid explicit standoff experiment bounds')
    state = json.loads((args.capture/'state.json').read_text())
    old = json.loads((args.source_capture/'state.json').read_text())
    carry = json.loads(args.carry_command.read_text())
    episode, step = state['observation_id'].split(':')
    old_episode, old_step = old['observation_id'].split(':')
    if episode != old_episode or int(step) <= int(old_step) or carry['observation_id'] != old['observation_id']:
        raise ValueError('unrelated or nonhistorical sensor geometry')
    measurements = carry['measurements']
    if any(m['observation_id'] != old['observation_id'] for m in measurements.values()):
        raise ValueError('unbound measurements')
    measured_feature = np.array([*measurements['held_feature']['surface_point_world_m'], 1.])
    predicted = (pose_matrix(state['hand_pose_world']) @ np.linalg.inv(pose_matrix(old['hand_pose_world'])) @ measured_feature)[:3]
    slot = np.asarray(measurements['slot_feature']['surface_point_world_m'])
    gap = float(predicted[2]-slot[2])
    lateral = float(np.linalg.norm(predicted[:2]-slot[:2]))
    if not np.isfinite([gap, lateral]).all() or gap-args.descent_m < args.minimum_gap_m or lateral > .03:
        raise ValueError('estimated geometry does not support bounded closer standoff')
    target = [*state['hand_pose_world'][:3], *carry['phases'][-1]['hand_pose_world'][3:]]
    target[2] -= args.descent_m
    evidence = dict(observation_id=state['observation_id'], source_observation_id=old['observation_id'],
        last_measured_slot_surface_world_m=slot.tolist(), predicted_held_feature_world_m=predicted.tolist(),
        predicted_vertical_gap_m=gap, predicted_lateral_error_m=lateral,
        assumptions='Stationary socket and no grasp slip. Predicted point is NOT a fresh measurement or whole-object clearance.',
        proposed_descent_m=args.descent_m, minimum_estimated_gap_m=args.minimum_gap_m,
        predicted_remaining_vertical_gap_m=gap-args.descent_m)
    if args.fresh_feature:
        feature = json.loads(args.fresh_feature.read_text())
        if (feature['observation_id'] != state['observation_id']
                or feature['measurement']['observation_id'] != state['observation_id']):
            raise ValueError('fresh feature is not from current observation')
        fresh_point = finite_vector(feature['measurement']['surface_point_world_m'], 3)
        if fresh_point[2]-slot[2]-args.descent_m < args.minimum_gap_m:
            raise ValueError('fresh point contradicts proposed remaining gap')
        evidence['fresh_feature_audit'] = feature
    candidate = dict(observation_id=state['observation_id'], reference_control_dt=1/15,
        phases=[dict(name='bounded_closer_standoff', hand_pose_world=target, finger_position_m=.012,
                     actions=max(90,int(np.ceil((args.descent_m/.0225+2)*15))))],
        finish=False, target_source='sensor-history rigid-grasp prediction plus fresh robot pose; operator-defined bounded closer look',
        limitations='Exploratory unknown clearance; no insertion, contact, seating, or slip-free certificate.', evidence=evidence)
    validate_plan(candidate, state['observation_id'], 180)
    prompt = (
        'Review a proposed CLOSER INSPECTION STANDOFF, not an insertion. Current RGB views follow '
        'an assisted grasp, elevated carry, and independent camera movement. All are simulator-only. '
        'Earlier RGB-D selected a held card surface and socket housing; robot proprioception propagates '
        'that feature under an UNVERIFIED rigid/no-slip grasp assumption. Read the estimates below as '
        'predictions, not object truth or collision clearance. No object state or evaluator is provided. '
        'The proposed action lowers the hand by the explicit distance in the evidence, preserving '
        'its commanded attitude and leaving the stated estimated gap above the historical socket '
        'surface. It does not close the gripper further or correct lateral position. '
        'External swept clearance is explicitly unknown in this authorized exploratory simulator test. '
        'Decide whether current visual evidence supports this bounded closer look. Do not demand '
        'insertion-level key alignment for a standoff, but choose inspect/stop for apparent slip, '
        'obstacle interference, incorrect target association, or inadequate evidence for this move. '
        'Return only JSON: observation_id, decision (approve_standoff/inspect/stop), evidence, uncertainty. '
        + json.dumps(evidence) + '\nCurrent robot state: ' + json.dumps(state))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        content.extend([{'type': 'text', 'text': 'CURRENT '+role}, {'type': 'image_url', 'image_url': {
            'url': 'data:image/png;base64,'+base64.b64encode((args.capture/f'{role}.png').read_bytes()).decode()}}])
    content.extend([{'type': 'text', 'text': 'HISTORICAL right camera at '+old['observation_id']+
                    '; previous socket view, NOT current clearance'}, {'type': 'image_url', 'image_url': {
            'url': 'data:image/png;base64,'+base64.b64encode((args.source_capture/'right.png').read_bytes()).decode()}}])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'candidate.json').write_text(json.dumps(candidate, indent=2)+'\n')
    (args.output/'messages.json').write_text(json.dumps([{'role': 'user', 'content': content}]))
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
