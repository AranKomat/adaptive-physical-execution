#!/usr/bin/env python3
"""Matched open-gripper guarded lift for separating baseline tracking from payload effects."""
import argparse
import os
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--height', type=float, default=.09)
    args = parser.parse_args()
    if not np.isfinite(args.height) or not 0 < args.height <= .09:
        raise ValueError('height must be in (0, .09] m')
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        metadata = client.call('/metadata')
        if metadata.get('real_hardware_supported') is not False or not metadata.get('local_stages_enabled'):
            raise ValueError('requires simulator local stages')
        if not metadata.get('contact_tracking_guard_enabled'):
            raise ValueError('worker does not advertise contact guard')
        obs = decode_observation(client.call('/reset', {'seed': 0}, mutating=True))
        write_json(args.output/'before.json', obs.public_state())
        target = obs.eef_pose.copy(); target[2] += args.height
        request = dict(observation_id=obs.key, hand_pose_world=target.tolist(),
                       gripper_open=1., max_steps=64,
                       target_source='matched open-gripper guarded tracking baseline',
                       contact_tracking_guard=True)
        envelope = dict(command_id=uuid4().hex, action=request)
        write_json(args.output/'request.json', envelope)
        result = decode_result(client.call('/local-stage', envelope, mutating=True))
        write_json(args.output/'receipt.json', result.receipt.to_dict())
        write_json(args.output/'after.json', result.observation.public_state())
        for role, pixels in result.observation.images.items():
            (args.output/f'after_{role}.png').write_bytes(png_bytes(pixels))
        write_json(args.output/'result.json', dict(
            terminal_reason=result.receipt.reason,
            executed_steps=result.receipt.executed_steps,
            endpoint_arrival=result.receipt.reason == 'local stage arrived',
            comparison='open gripper, same task/controller/guard, seed 0'))
        print(result.receipt.to_dict(), flush=True)
    finally:
        client.close()


if __name__ == '__main__':
    main()
