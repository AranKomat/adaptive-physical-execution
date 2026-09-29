#!/usr/bin/env python3
"""Execute one reviewed inclined recovery standoff; never descend or close."""
import argparse
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.geometry import matrix_pose, pose_error, pose_matrix, quat_mul, rotvec_to_quat
from physical_exec.imaging import png_bytes
from physical_exec.kinematics import URDFKinematics
from physical_exec.local_stage import validate_local_stage
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    review = json.loads(args.review.read_text())
    if (review['decision'] != 'approve_standoff' or review['contact_authorized'] is not False
            or review['observation_id'] != audit['observation_id']):
        raise ValueError('Requires matching standoff-only review')
    index = review['candidate_index']
    if type(index) is not int or not 0 <= index < len(audit['candidates']):
        raise ValueError('Invalid candidate selection')
    target = np.asarray(audit['candidates'][index]['hand_pose_world'], dtype=float).copy()
    target[2] += .06
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        obs = decode_observation(client.call('/observe'))
        if (meta.get('real_hardware_supported') is not False
                or not meta.get('local_stages_enabled')
                or not meta.get('contact_tracking_guard_enabled')
                or not meta.get('continuous_transit_enabled')):
            raise ValueError('Requires guarded continuous simulator worker')
        if obs.key != audit['observation_id'] or abs(obs.control_dt - 1/15) > 1e-8:
            raise ValueError('Stale observation or unsupported control cadence')
        opening = meta.get('last_gripper_command')
        if opening is None or opening < .999:
            raise ValueError('Requires already open gripper')
        write_json(args.output/'before.json', obs.public_state())
        kin = URDFKinematics.from_urdf(Path(__file__).resolve().parents[1] /
            'upstream/EmbodiedSWE/robobench/robots/assets/franka/panda_kinematics.urdf')
        base = matrix_pose(pose_matrix(obs.eef_pose) @ np.linalg.inv(pose_matrix(kin.fk(obs.joints))))
        stages = []
        start, seed = obs.eef_pose.copy(), obs.joints.copy()
        for name, end in [('reorient', np.r_[start[:3], target[3:]]), ('standoff', target)]:
            error = pose_error(start, end)
            count = max(1, math.ceil(np.linalg.norm(error[:3])/.04),
                        math.ceil(np.linalg.norm(error[3:])/.23))
            for i in range(1, count+1):
                pose = np.r_[start[:3] + error[:3]*i/count,
                             quat_mul(rotvec_to_quat(error[3:]*i/count), start[3:])]
                ik = kin.solve(pose, seed, base, iterations=300)
                if not ik.converged:
                    raise ValueError(f'Robot-only waypoint IK failed: {name}/{i}')
                seed = ik.joints
                stages.append(dict(phase=name, hand_pose_world=pose.tolist(),
                                   settle_at_end=i == count))
            start = end.copy()
        if len(stages) > 16:
            raise ValueError('Exceeds 16-stage budget')
        predicted = obs
        for stage in stages:
            pose = validate_local_stage(dict(observation_id=predicted.key,
                hand_pose_world=stage['hand_pose_world'], gripper_open=opening,
                max_steps=64, settle_at_end=stage['settle_at_end'],
                contact_tracking_guard=True, target_source='recovery standoff preflight'), predicted)
            predicted = replace(predicted, eef_pose=pose)
        write_json(args.output/'declared_sequence.json', dict(
            observation_id=obs.key, candidate_index=index, stages=stages,
            max_actions=64*len(stages), grip=opening, contact_authorized=False,
            clearance='unknown; simulator-only exploratory',
            ik='Robot-only endpoint checks, not swept collision qualification'))
        if not args.execute:
            print(f'Preflight passed: {len(stages)} stages, at most {64*len(stages)} actions')
            return
        for number, stage in enumerate(stages):
            action = dict(observation_id=obs.key, hand_pose_world=stage['hand_pose_world'],
                gripper_open=opening, max_steps=64, settle_at_end=stage['settle_at_end'],
                contact_tracking_guard=True,
                target_source='Reviewed inclined recovery standoff; open hand; unknown clearance; no descent/closure/retry')
            validate_local_stage(action, obs)
            envelope = dict(command_id=uuid4().hex, action=action)
            write_json(args.output/f'{number:02d}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            write_json(args.output/f'{number:02d}_receipt.json', result.receipt.to_dict())
            obs = result.observation
            write_json(args.output/f'{number:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{number:02d}_{role}.png').write_bytes(png_bytes(pixels))
            print(stage['phase'], result.receipt.to_dict(), flush=True)
            expected = 'local stage arrived' if stage['settle_at_end'] else 'transit waypoint passed'
            if result.receipt.reason != expected:
                write_json(args.output/'result.json', dict(observation_id=obs.key,
                    status='stopped_without_retry', failed_stage=number,
                    reason=result.receipt.reason, grasp_verified=False, contact_authorized=False))
                raise RuntimeError('Nonarrival or guard stop; no retry or further stage')
        write_json(args.output/'result.json', dict(observation_id=obs.key,
            status='standoff_arrived', grasp_verified=False, contact_authorized=False))
    finally:
        client.close()


if __name__ == '__main__':
    main()
