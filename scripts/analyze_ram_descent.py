#!/usr/bin/env python3
"""Reconstruct a retained RAM descent from rigid wrist calibration, not object state."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import matrix_pose, pose_matrix
from physical_exec.osc_reference import ramped_pose_target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--wrist-depth', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    stages = json.loads((args.run/'declared_sequence.json').read_text())
    indices = [i for i, stage in enumerate(stages) if stage['name'] == 'preclosure']
    last = json.loads((args.run/f'{indices[-1]:02d}_observation.json').read_text())
    episode = last['episode_id']

    def camera(step):
        value = json.loads((args.wrist_depth/f'{step:06d}.json').read_text())
        if value['observation_id'] != f'{episode}:{step}':
            raise ValueError('Detached wrist calibration')
        return pose_matrix(value['camera_position_world'] +
                           value['camera_quaternion_world_wxyz_optical'])

    camera_to_hand = np.linalg.inv(camera(last['step'])) @ pose_matrix(last['eef_pose_world_xyz_wxyz'])
    measured = lambda step: matrix_pose(camera(step) @ camera_to_hand)
    integral = np.zeros(3)
    samples = []
    residuals = []
    ramp_start = None
    for index in indices:
        receipt = json.loads((args.run/f'{index:02d}_receipt.json').read_text())
        step = int(receipt['observation_id'].rsplit(':', 1)[1])
        state = json.loads((args.run/f'{index-1:02d}_observation.json').read_text())
        if state['observation_id'] != receipt['observation_id']:
            raise ValueError('Noncontiguous descent')
        residuals.append(float(np.linalg.norm(measured(step)-state['eef_pose_world_xyz_wxyz'])))
        if ramp_start is None:
            ramp_start = np.array(state['eef_pose_world_xyz_wxyz'])
        target = np.array(stages[index]['hand_pose_world'])
        dt = state['control_dt_seconds']
        for offset in range(receipt['executed_steps']):
            waypoint = ramped_pose_target(ramp_start, target, offset+1, .0225*dt, .06*dt)
            error = waypoint[:3]-measured(step+offset)[:3]
            # Replay the OLD controller explicitly; do not use its changed implementation.
            integral = np.clip(integral + .525*dt*error, -.03, .03)
            samples.append(dict(step=step+offset+1, integral_z_m=float(integral[2]),
                measured_z_m=float(measured(step+offset+1)[2]), ramp_z_m=float(waypoint[2])))
        ramp_start = target
    report = dict(episode=episode, endpoint_calibration_residuals=residuals,
        limitation='Rigid wrist-to-hand transform inferred from terminal proprioception; '
                   'integral is reconstructed, not logged. No counterfactual physical validation.',
        samples=samples)
    if args.output:
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
        print(args.output)
    else:
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
