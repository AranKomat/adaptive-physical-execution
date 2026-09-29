#!/usr/bin/env python3
"""Export a recorded public observation and matching legal RGB-D, without evaluator data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--recordings', type=Path, required=True)
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stem = f'{args.step:06d}'
    state = json.loads((args.run/'observations'/f'{stem}.json').read_text())
    sources = []
    for role in ('left', 'right', 'wrist'):
        image = args.run/state['images'][role]['path']
        if hashlib.sha256(image.read_bytes()).hexdigest() != state['images'][role]['sha256']:
            raise ValueError('Recorded image checksum mismatch')
        base = args.recordings/state['episode_id']/f'{role}_depth'/stem
        calibration = base.with_suffix('.json')
        if json.loads(calibration.read_text())['observation_id'] != state['observation_id']:
            raise ValueError('Depth calibration observation mismatch')
        sources.extend([(image, f'{role}.png'), (calibration, f'{role}_calibration.json'),
                        (base.with_suffix('.npy'), f'{role}_depth.npy')])
    if not all(source.is_file() for source, _ in sources):
        raise ValueError('Missing recorded sensor input')
    args.output.mkdir(parents=True, exist_ok=False)
    public = {key: state[key] for key in ('observation_id', 'joint_names', 'joints_rad')}
    public['hand_pose_world'] = state['eef_pose_world_xyz_wxyz']
    (args.output/'state.json').write_text(json.dumps(public, indent=2)+'\n')
    for source, name in sources:
        shutil.copyfile(source, args.output/name)


if __name__ == '__main__':
    main()
