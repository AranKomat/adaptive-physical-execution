#!/usr/bin/env python3
"""One bounded retreat, with per-latch stops and explicit operator image review."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.geometry import finite_vector, pose_error
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    if (review['decision'] != 'retreat' or review['preserve_orientation'] is not True
            or review['preserve_open_grip'] is not True):
        raise ValueError('Requires open-hand fixed-orientation retreat review')
    delta = finite_vector(review['translation_world_m'], 3)
    distance = np.linalg.norm(delta)
    if not 0 < distance <= .03:
        raise ValueError('Retreat must be within 30mm')
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        obs = decode_observation(client.call('/observe'))
        if (meta.get('real_hardware_supported') is not False
                or not meta.get('continuous_transit_enabled')
                or not meta.get('contact_tracking_guard_enabled')):
            raise ValueError('Requires guarded continuous simulator worker')
        if obs.key != review['observation_id'] or abs(obs.control_dt - 1/15) > 1e-8:
            raise ValueError('Stale review or unsupported cadence')
        opening = meta.get('last_gripper_command')
        if opening is None or opening < .999:
            raise ValueError('Requires already open hand')
        origin = obs.eef_pose.copy()
        count = math.ceil(distance/.0014)
        direction = delta/distance
        write_json(args.output/'plan.json', dict(observation_id=obs.key,
            origin_pose=origin.tolist(), translation_m=delta.tolist(), max_actions=count,
            orientation_stop_rad=.02, progress_stop='two consecutive nonpositive projections',
            contact_authorized=False, clearance='unknown; simulator-only exploratory'))
        write_json(args.output/'before.json', obs.public_state())
        stagnant = 0
        for index in range(1, count+1):
            target = origin.copy()
            target[:3] += delta*index/count
            envelope = dict(command_id=uuid4().hex, action=dict(observation_id=obs.key,
                hand_pose_world=target.tolist(), gripper_open=opening, max_steps=1,
                settle_at_end=False, contact_tracking_guard=True,
                target_source='Reviewed retreat: single control latch, fixed attitude/open hand, unknown clearance'))
            write_json(args.output/f'{index:02d}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            previous = obs
            obs = result.observation
            write_json(args.output/f'{index:02d}_receipt.json', result.receipt.to_dict())
            write_json(args.output/f'{index:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{index:02d}_{role}.png').write_bytes(png_bytes(pixels))
            progress = float(np.dot(obs.eef_pose[:3]-previous.eef_pose[:3], direction))
            stagnant = stagnant+1 if progress <= 0 else 0
            angle = float(np.linalg.norm(pose_error(obs.eef_pose, origin)[3:]))
            reason = None
            if result.receipt.reason != 'transit waypoint passed':
                reason = result.receipt.reason
            elif angle > .02:
                reason = 'orientation deviation exceeded 0.02rad'
            elif obs.gripper_open < .999:
                reason = 'measured gripper aperture below open threshold'
            elif stagnant >= 2:
                reason = 'retreat progress stalled/reversed for two updates'
            print(json.dumps(dict(step=index, total=count, observation_id=obs.key,
                progress_m=progress, orientation_error_rad=angle, stop_reason=reason)), flush=True)
            if reason:
                write_json(args.output/'result.json', dict(observation_id=obs.key,
                    status='stopped_without_retry', reason=reason, actions=index))
                return
            if index < count:
                print('Inspect saved images; enter continue or stop. EOF stops without retry.', flush=True)
                try:
                    decision = input().strip()
                except EOFError:
                    decision = 'stop'
                write_json(args.output/f'{index:02d}_visual_review.json', dict(decision=decision))
                if decision != 'continue':
                    write_json(args.output/'result.json', dict(observation_id=obs.key,
                        status='stopped_by_visual_review', actions=index))
                    return
        write_json(args.output/'result.json', dict(observation_id=obs.key,
            status='bounded_retreat_finished', actions=count,
            actual_translation_m=(obs.eef_pose[:3]-origin[:3]).tolist(),
            target_error_m=float(np.linalg.norm(obs.eef_pose[:3]-origin[:3]-delta)),
            clearance_verified=False, grasp_verified=False))
    finally:
        client.close()


if __name__ == '__main__':
    main()
