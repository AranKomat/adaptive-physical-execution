#!/usr/bin/env python3
"""Measure current feature samples without refining pixels or authorizing motion."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.depth import surface_point
from physical_exec.trace import write_json


def measure(capture, response):
    state = json.loads((capture/'state.json').read_text())
    if response['observation_id'] != state['observation_id']:
        raise ValueError('Feature selection is stale')
    result = dict(observation_id=state['observation_id'],motion_authorized=False,
        limitation='Surface samples only; axes are undirected, not mating endpoints, gap centerlines or clearance.')
    for name in ('connector','socket'):
        feature = response[name]
        samples = feature['samples']
        if not isinstance(samples,list) or len(samples)>8:
            raise ValueError('Invalid sample count')
        measured = []
        for sample in samples:
            role = sample['camera']
            if role not in ('left','right','wrist'):
                raise ValueError('Invalid camera')
            calibration = json.loads((capture/f'{role}_calibration.json').read_text())
            if calibration['observation_id'] != state['observation_id']:
                raise ValueError('Calibration is stale')
            record = dict(sample)
            try:
                record['measurement'] = surface_point(np.load(capture/f'{role}_depth.npy',allow_pickle=False),
                    calibration,sample['pixel_uv'],radius=1,max_spread_m=.01)
            except ValueError as exc:
                record['rejected'] = str(exc)
            measured.append(record)
        summary = dict(visual_status=feature['status'],samples=measured)
        if len(measured)==2 and all('measurement' in m for m in measured):
            points = np.array([m['measurement']['surface_point_world_m'] for m in measured])
            vector = points[1]-points[0]
            distance = float(np.linalg.norm(vector))
            summary['sample_separation_m'] = distance
            if distance > .005:
                summary['undirected_surface_axis_world'] = (vector/distance).tolist()
        result[name] = summary
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--response',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = measure(args.capture,json.loads(args.response.read_text()))
    if args.output.exists():
        raise ValueError('Refusing to overwrite measurements')
    write_json(args.output,result)
    print(json.dumps(result,indent=2))
