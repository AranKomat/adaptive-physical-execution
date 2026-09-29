#!/usr/bin/env python3
"""Recover hand motion from calibrated rigid wrist-camera poses; no scene-object state."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import pose_matrix, matrix_pose, pose_error


def camera_pose(value):
    return pose_matrix([*value['camera_position_world'], *value['camera_quaternion_world_wxyz_optical']])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--recording',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    before = json.loads((args.probe/'before.json').read_text())
    after = json.loads((args.probe/'after.json').read_text())
    if before['episode_id'] != after['episode_id'] or after['step'] <= before['step']:
        raise ValueError('Need an ordered same-episode contact interval')
    poses = []
    hand_to_camera = None
    for step in range(before['step'],after['step']+1):
        calibration = json.loads((args.recording/'wrist_depth'/f'{step:06d}.json').read_text())
        if calibration['observation_id'] != f'{before["episode_id"]}:{step}':
            raise ValueError('Stale calibration')
        transform = camera_pose(calibration)
        if hand_to_camera is None:
            hand_to_camera = np.linalg.inv(pose_matrix(before['eef_pose_world_xyz_wxyz']))@transform
        poses.append(matrix_pose(transform@np.linalg.inv(hand_to_camera)))
    endpoint_error = pose_error(poses[-1],after['eef_pose_world_xyz_wxyz'])
    if np.linalg.norm(endpoint_error[:3]) > .001 or np.linalg.norm(endpoint_error[3:]) > .005:
        raise ValueError('Recovered endpoint disagrees with measured hand; rigid calibration assumption invalid')
    tail = poses[-16:]
    differences = [pose_error(a,b) for i,a in enumerate(tail) for b in tail[i+1:]]
    result = {
        'start_observation_id':before['observation_id'],'end_observation_id':after['observation_id'],
        'recovered_endpoint_error':endpoint_error.tolist(),
        'last_window_seconds':(len(tail)-1)*before['control_dt_seconds'],
        'last_window_position_diameter_m':max(float(np.linalg.norm(d[:3])) for d in differences),
        'last_window_rotation_diameter_rad':max(float(np.linalg.norm(d[3:])) for d in differences),
        'target_error_by_step':[{'step':before['step']+i,
                                'pose_error':pose_error(p,before['eef_pose_world_xyz_wxyz']).tolist()}
                               for i,p in enumerate(poses)],
        'limitation':'Derived robot motion only, assuming fixed calibrated wrist mount. '
                     'No force, object retention, grip stability, clearance or success inference.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'target_error_by_step'},indent=2))


if __name__ == '__main__':
    main()
