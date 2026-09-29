#!/usr/bin/env python3
"""Execute a fresh reviewed elevated carry on the held episode; never reset/retry."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.carry import carry_stages, standoff_stages
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exploratory-standoff',action='store_true',
                        help='Current feature measurements; <=10 cm down, >=12 cm nominal standoff, no insertion')
    parser.add_argument('--near-standoff',action='store_true',
                        help='With exploratory-standoff: <=6cm down, >=6cm nominal gap, matched endpoint required')
    args = parser.parse_args()
    if args.near_standoff and not args.exploratory_standoff:
        parser.error('--near-standoff requires --exploratory-standoff')
    plan = json.loads(args.plan.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        if (meta.get('real_hardware_supported') is not False or not meta.get('local_stages_enabled')
                or not meta.get('continuous_transit_enabled')):
            raise ValueError('Requires simulator continuous local stages')
        obs = decode_observation(client.call('/observe'))
        compiler = standoff_stages if args.exploratory_standoff else carry_stages
        stages = compiler(plan, obs.key, obs.eef_pose, meta.get('last_gripper_command'),
                          **({'near':args.near_standoff} if args.exploratory_standoff else {}))
        write_json(args.output/'source_plan.json', plan)
        write_json(args.output/'declared_sequence.json', stages)
        write_json(args.output/'initial.json', obs.public_state())
        actions = 0
        for i, stage in enumerate(stages):
            request = dict(command_id=uuid4().hex, action=dict(stage, observation_id=obs.key))
            write_json(args.output/f'{i:02d}_request.json', request)
            result = decode_result(client.call('/local-stage', request, mutating=True))
            obs = result.observation
            write_json(args.output/f'{i:02d}_receipt.json', result.receipt.to_dict())
            write_json(args.output/f'{i:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{i:02d}_{role}.png').write_bytes(png_bytes(pixels))
            actions += result.receipt.executed_steps
            print(result.receipt.to_dict(), flush=True)
            expected = 'local stage arrived' if stage['settle_at_end'] else 'transit waypoint passed'
            if result.receipt.reason != expected:
                raise RuntimeError('Carry nonarrival; no retry or subsequent stage')
        write_json(args.output/'result.json', dict(final_observation_id=obs.key, actions=actions,
                   insertion_verified=False, limitation='Endpoint only; fresh visual review required'))
    finally:
        client.close()


if __name__ == '__main__':
    main()
