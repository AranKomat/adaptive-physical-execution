#!/usr/bin/env python3
"""Fresh simulator-only hold then 1 cm upward correction; no model calls or object contact intended."""
import argparse
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.transport import LocalClient, decode_observation, decode_result
from physical_exec.trace import write_json
from physical_exec.imaging import png_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--contact-tracking-guard', action='store_true',
                        help='qualify guard-enabled free-space execution; does not test a contact stall')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        metadata = client.call('/metadata')
        if not metadata.get('local_stages_enabled') or metadata.get('real_hardware_supported') is not False:
            raise ValueError('requires explicitly enabled simulation worker')
        if args.contact_tracking_guard and not metadata.get('contact_tracking_guard_enabled'):
            raise ValueError('worker does not advertise contact tracking guard')
        write_json(args.output/'metadata.json', metadata)
        obs = decode_observation(client.call('/reset', {'seed': 0}, mutating=True))
        write_json(args.output/'initial.json', obs.public_state())
        for index, (name, steps, dz) in enumerate((('hold',30,0.), ('upward_1cm',60,.01))):
            target = obs.eef_pose.copy()
            target[2] += dz
            request = dict(observation_id=obs.key, hand_pose_world=target.tolist(),
                           gripper_open=1., max_steps=steps, target_source='robot-only '+name+' qualification; unknown clearance')
            if args.contact_tracking_guard:
                request['contact_tracking_guard'] = True
            envelope = dict(command_id=uuid4().hex, action=request)
            write_json(args.output/f'{index}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            write_json(args.output/f'{index}_receipt.json', result.receipt.to_dict())
            obs = result.observation
            write_json(args.output/f'{index}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{index}_{role}.png').write_bytes(png_bytes(pixels))
            print(result.receipt.to_dict(), flush=True)
            if result.receipt.reason != 'local stage arrived':
                raise RuntimeError('stage did not arrive; stop without subsequent motion')
    finally:
        client.close()


if __name__ == '__main__':
    main()
