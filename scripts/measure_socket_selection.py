#!/usr/bin/env python3
"""Measure a fresh visual socket selection; never create a motion command."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.depth import surface_point


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--response', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.capture / 'state.json').read_text())
    response = json.loads(args.response.read_text())
    if response['observation_id'] != state['observation_id'] or response['decision'] != 'localized':
        raise ValueError('requires fresh localized socket selection')
    measurements = {}
    for name in ('center', 'end_a', 'end_b'):
        feature = response[name]
        role = feature['camera']
        if role not in ('left', 'right', 'wrist'):
            raise ValueError('invalid camera')
        calibration = json.loads((args.capture / f'{role}_calibration.json').read_text())
        if calibration['observation_id'] != state['observation_id']:
            raise ValueError('stale calibration')
        try:
            measurements[name] = surface_point(
                np.load(args.capture / f'{role}_depth.npy'), calibration,
                feature['pixel_uv'], radius=1, max_spread_m=.01)
        except ValueError as exc:
            measurements[name] = {'error': str(exc), 'pixel_uv': feature['pixel_uv']}
    result = dict(observation_id=state['observation_id'], measurements=measurements,
                  motion_authorized=False,
                  limitation='Housing samples are not insertion gap, full endpoint correspondence, or clearance.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
