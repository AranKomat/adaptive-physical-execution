#!/usr/bin/env python3
"""One explicitly exploratory simulator contact stage; not visual-gate approval or autonomous recovery."""
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
    parser.add_argument('--mode', choices=['close','lift_5cm'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        metadata = client.call('/metadata')
        if metadata.get('real_hardware_supported') is not False or not metadata.get('local_stages_enabled'):
            raise ValueError('Requires opt-in simulator')
        obs = decode_observation(client.call('/observe'))
        if obs.key != args.observation_id:
            raise ValueError('Observation changed; no automatic retry')
        write_json(args.output/'before.json', obs.public_state())
        for role,pixels in obs.images.items():
            (args.output/f'before_{role}.png').write_bytes(png_bytes(pixels))
        target = obs.eef_pose.copy()
        if args.mode == 'lift_5cm':
            target[2] += .05
        envelope = dict(command_id=uuid4().hex, action=dict(observation_id=obs.key,
            hand_pose_world=target.tolist(),gripper_open=.3,max_steps=64,
            target_source='Operator-scoped exploratory contact probe; unknown clearance; NOT visual-gate approval'))
        write_json(args.output/'request.json', envelope)
        result = decode_result(client.call('/local-stage',envelope,mutating=True))
        write_json(args.output/'receipt.json',result.receipt.to_dict())
        write_json(args.output/'after.json',result.observation.public_state())
        for role,pixels in result.observation.images.items():
            (args.output/f'after_{role}.png').write_bytes(png_bytes(pixels))
        print(result.receipt.to_dict(),flush=True)
        if result.receipt.reason != 'local stage arrived':
            raise RuntimeError('Stop: endpoint did not arrive; no retry')
    finally:
        client.close()


if __name__ == '__main__':
    main()
