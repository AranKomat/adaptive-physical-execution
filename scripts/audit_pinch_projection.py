#!/usr/bin/env python3
"""Project nominal robot pad center into retained calibrated images; no object truth."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.geometry import pose_matrix, quat_to_matrix
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation', type=Path, action='append', required=True)
    parser.add_argument('--recording', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for path in args.observation:
        obs = json.loads(path.read_text())
        if obs['robot'] != 'franka' or obs['eef_frame'] != 'panda_hand':
            raise ValueError('only pinned Panda pad-center convention supported')
        point = (pose_matrix(obs['eef_pose_world_xyz_wxyz']) @ np.array([0, 0, .1034, 1]))[:3]
        views = {}
        for role in ('left', 'right', 'wrist'):
            calibration = json.loads((args.recording/f'{role}_depth'/f'{obs["step"]:06d}.json').read_text())
            if calibration['observation_id'] != obs['observation_id']:
                raise ValueError('calibration is not from this observation')
            camera = quat_to_matrix(calibration['camera_quaternion_world_wxyz_optical']).T @ (
                point - np.asarray(calibration['camera_position_world']))
            pixel = np.asarray(calibration['intrinsic_matrix']) @ camera
            uv = pixel[:2] / pixel[2] if camera[2] > 0 else None
            with Image.open(path.parent.parent / obs['images'][role]['path']) as im:
                width, height = im.size
            views[role] = dict(pixel_uv=None if uv is None else uv.tolist(),
                optical_depth_m=float(camera[2]),
                in_image=bool(uv is not None and 0 <= uv[0] < width and 0 <= uv[1] < height))
        rows.append(dict(observation_id=obs['observation_id'], nominal_pinch_world_m=point.tolist(), views=views))
    result = dict(robot_offset_hand_m=[0, 0, .1034], measurements=rows,
        limitation='Nominal robot point projection only. In-frame does not imply visible/unoccluded; no target pose, contact, clearance, or grasp proof.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
