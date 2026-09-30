#!/usr/bin/env python3
"""One elevated open-hand wrist-camera look toward a legal sensor region, not a grasp."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import finite_vector, pose_matrix, quat_mul, rotvec_to_quat
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def inspection_target(hand, calibration, point):
    hand = finite_vector(hand, 7)
    point = finite_vector(point, 3)
    camera = np.r_[calibration['camera_position_world'],
                   calibration['camera_quaternion_world_wxyz_optical']]
    transform = pose_matrix(camera)
    direction = point-transform[:3, 3]
    distance = np.linalg.norm(direction)
    if hand[2] < .35 or not .1 <= distance <= .6:
        raise ValueError('Inspection requires elevated hand and nearby visible sensor region')
    forward = transform[:3, 2]
    axis = np.cross(forward, direction/distance)
    angle = np.arccos(np.clip(np.dot(forward, direction/distance), -1., 1.))
    if np.linalg.norm(axis) < 1e-8 or angle < .01:
        raise ValueError('No supported look rotation')
    rotation = axis/np.linalg.norm(axis)*min(float(angle), .2)
    return np.r_[hand[:3], quat_mul(rotvec_to_quat(rotation), hand[3:])]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url', required=True)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--region-plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    state = json.loads((args.capture/'state.json').read_text())
    calibration = json.loads((args.capture/'wrist_calibration.json').read_text())
    plan = json.loads(args.region_plan.read_text())
    expected = state['observation_id']
    if calibration['observation_id'] != expected or plan['measured_surface']['observation_id'] != expected:
        raise ValueError('Sensor region and camera calibration must match capture')
    target = inspection_target(state['hand_pose_world'], calibration,
                               plan['measured_surface']['surface_point_world_m'])
    args.output.mkdir(parents=True, exist_ok=False)
    stages = [state['hand_pose_world'], target.tolist()]
    write_json(args.output/'plan.json', dict(observation_id=expected, poses=stages,
        opening=1., max_actions=128, rotation_bound_rad=.2, contact_authorized=False,
        clearance='unknown; simulator-only', region_source=plan,
        limitation='Coarse sensor region for camera aiming, not verified top-face identity or grasp target'))
    if not args.execute:
        return
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        if (meta.get('real_hardware_supported') is not False or not meta.get('local_stages_enabled')
                or not meta.get('contact_tracking_guard_enabled')):
            raise ValueError('Requires guarded simulator')
        obs = decode_observation(client.call('/observe'))
        if obs.key != expected or np.linalg.norm(obs.eef_pose-np.array(state['hand_pose_world'])) > 1e-6:
            raise ValueError('Observation changed; no motion')
        for i, pose in enumerate(stages):
            request = dict(command_id=uuid4().hex, action=dict(observation_id=obs.key,
                hand_pose_world=pose, gripper_open=1., max_steps=64,
                contact_tracking_guard=True,
                target_source='Operator wrist inspection toward coarse legal sensor region; unknown clearance; no grasp'))
            write_json(args.output/f'{i:02d}_request.json', request)
            result = decode_result(client.call('/local-stage', request, mutating=True))
            obs = result.observation
            write_json(args.output/f'{i:02d}_receipt.json', result.receipt.to_dict())
            write_json(args.output/f'{i:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{i:02d}_{role}.png').write_bytes(png_bytes(pixels))
            print(result.receipt.to_dict(), flush=True)
            if result.receipt.reason != 'local stage arrived':
                raise RuntimeError('Inspection nonarrival; no retry or subsequent motion')
        write_json(args.output/'result.json', dict(observation_id=obs.key, contact_authorized=False))
    finally:
        client.close()


if __name__ == '__main__':
    main()
