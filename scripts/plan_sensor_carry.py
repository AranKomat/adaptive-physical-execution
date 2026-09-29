#!/usr/bin/env python3
"""Compile a reviewed feature-relative elevated carry, never an insertion."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.depth import surface_point
from physical_exec.osc_reference import validate_plan
from physical_exec.trace import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--response',type=Path,required=True)
    p.add_argument('--previous-command',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    state = json.loads((args.capture/'state.json').read_text())
    response = json.loads(args.response.read_text())
    if response['observation_id'] != state['observation_id'] or response['decision'] != 'carry_above_slot':
        raise ValueError('No fresh carry selection')
    measurements = {}
    for name in ('held_feature','slot_feature'):
        feature = response[name]
        role = feature['camera']
        if role not in ('left','right','wrist'):
            raise ValueError('invalid camera')
        calibration = json.loads((args.capture/f'{role}_calibration.json').read_text())
        if calibration['observation_id'] != state['observation_id']:
            raise ValueError('stale calibration')
        measurements[name] = surface_point(np.load(args.capture/f'{role}_depth.npy',allow_pickle=False),
            calibration,feature['pixel_uv'],radius=1,max_spread_m=.01)
    hand = np.asarray(state['hand_pose_world'][:3])
    held = np.asarray(measurements['held_feature']['surface_point_world_m'])
    slot = np.asarray(measurements['slot_feature']['surface_point_world_m'])
    if np.linalg.norm(hand-held) > .35:
        raise ValueError('selected held feature too far from hand')
    target = hand + slot-held + [0,0,.23]
    target[2] = max(target[2],hand[2])
    delta = target-hand
    if np.linalg.norm(delta) > .5:
        raise ValueError('carry exceeds bounded local workcell displacement')
    previous = json.loads(args.previous_command.read_text())
    if previous['observation_id'].split(':')[0] != state['observation_id'].split(':')[0]:
        raise ValueError('previous command is from another episode')
    # Preserve the commanded attitude, not the biased measured attitude, across stages.
    orientation = previous['phases'][-1]['hand_pose_world'][3:]
    segments = max(1,math.ceil(np.linalg.norm(delta)/.20))
    duration = np.linalg.norm(delta)/segments/.0225 + 2.
    steps = math.ceil(duration*15)
    phases = [dict(name=f'elevated_carry_{i}', hand_pose_world=[*(hand+delta*i/segments),*orientation],
                   finger_position_m=.012,actions=steps) for i in range(1,segments+1)]
    value = dict(observation_id=state['observation_id'],reference_control_dt=1/15,
                 phases=phases,finish=False,measurements=measurements,
                 target_source='fresh Astra feature selections plus legal RGB-D; relative translation',
                 limitations='Coarse carry only, no descent. 23 cm feature standoff and never lower hand. '
                 'Unknown swept clearance; semantic slot identity and precise alignment unverified.')
    validate_plan(value,state['observation_id'],700)
    write_json(args.output,value)
    print(json.dumps(value,indent=2))


if __name__ == '__main__':
    main()
