#!/usr/bin/env python3
"""Persist a worker's public observation; optional explicit reset, no control actions."""
import argparse
import hashlib
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reset', action='store_true', help='Only for an explicitly fresh worker')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        if args.reset:
            obs = decode_observation(client.call('/reset', {'seed':0}, mutating=True))
        else:
            obs = decode_observation(client.call('/observe'))
        (args.output/'frames').mkdir()
        (args.output/'observations').mkdir()
        state = obs.public_state()
        state['images'] = {}
        for role, pixels in obs.images.items():
            relative = f'frames/{obs.seq:06d}_{role}.png'
            data = png_bytes(pixels)
            (args.output/relative).write_bytes(data)
            state['images'][role] = {'path':relative, 'sha256':hashlib.sha256(data).hexdigest()}
        write_json(args.output/'observations'/f'{obs.seq:06d}.json', state)
        print(obs.key)
    finally:
        client.close()


if __name__ == '__main__':
    main()
