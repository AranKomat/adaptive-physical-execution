#!/usr/bin/env python3
"""One observation-bound idealized camera move while holding the arm and gripper."""
import argparse
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--observation-id', required=True)
    parser.add_argument('--eye', nargs=3, type=float, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        if not meta.get('inspection_camera_enabled') or meta.get('real_hardware_supported') is not False:
            raise ValueError('Requires opt-in simulator inspection camera')
        opening = meta.get('last_gripper_command')
        if opening is None:
            raise ValueError('Requires a previously established gripper command')
        obs = decode_observation(client.call('/observe'))
        if obs.key != args.observation_id:
            raise ValueError('Stale inspection request; no reset or retry')
        write_json(args.output/'before.json', obs.public_state())
        for role, pixels in obs.images.items():
            (args.output/f'before_{role}.png').write_bytes(png_bytes(pixels))
        envelope = dict(command_id=uuid4().hex, action=dict(
            observation_id=obs.key, hand_pose_world=obs.eef_pose.tolist(),
            gripper_open=opening, max_steps=64, camera_eye_world=args.eye,
            target_source='Operator-selected idealized inspection-camera move; arm hold; unknown clearance'))
        write_json(args.output/'request.json', envelope)
        result = decode_result(client.call('/local-stage', envelope, mutating=True))
        write_json(args.output/'receipt.json', result.receipt.to_dict())
        write_json(args.output/'after.json', result.observation.public_state())
        for role, pixels in result.observation.images.items():
            (args.output/f'after_{role}.png').write_bytes(png_bytes(pixels))
        print(result.receipt.to_dict(), flush=True)
        if result.receipt.executed_steps != 64 or result.receipt.reason != 'local stage arrived':
            raise RuntimeError('Inspection hold did not complete precisely; stop without retry')
    finally:
        client.close()


if __name__ == '__main__':
    main()
