#!/usr/bin/env python3
"""Bounded RGB pixel selection and legal depth feedback; never commands motion."""
import argparse
import base64
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.depth import surface_point
from physical_exec.geometry import pose_matrix


def measure(state, selection, recording):
    if selection['observation_id'] != state['observation_id']:
        raise ValueError('Stale pixel selection')
    samples = selection['samples']
    if not isinstance(samples, list) or len(samples) > 6:
        raise ValueError('At most six surface samples')
    transform = pose_matrix(state['eef_pose_world_xyz_wxyz'])
    results = []
    for sample in samples:
        role = sample['camera']
        if role not in ('left', 'right', 'wrist'):
            raise ValueError('Unknown camera')
        base = recording/f'{role}_depth'/f'{state["step"]:06d}'
        c = json.loads(base.with_suffix('.json').read_text())
        if c['observation_id'] != state['observation_id']:
            raise ValueError('Stale calibration')
        row = {'selection': sample}
        try:
            point = surface_point(np.load(base.with_suffix('.npy'), allow_pickle=False),
                                  c, sample['pixel_uv'], radius=1, max_spread_m=.01)
            hand = (np.linalg.inv(transform) @ np.r_[point['surface_point_world_m'], 1.])[:3]
            row.update(status='measured', measurement=point, point_hand_m=hand.tolist(),
                       offset_from_nominal_pinch_hand_m=(hand-[0, 0, .1034]).tolist())
        except ValueError as exc:
            row.update(status='rejected', reason=str(exc))
        results.append(row)
    return dict(observation_id=state['observation_id'], samples=results,
                limitation='Visible surfaces only, not semantic truth, hidden thickness, contact or clearance. '
                'Nominal pinch is hand [0,0,0.1034]; closing axis is hand Y. No executable targets.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--selection', type=Path)
    p.add_argument('--recording', type=Path)
    p.add_argument('--feedback', type=Path)
    a = p.parse_args()
    state = json.loads((a.capture/'state.json').read_text())
    if a.selection:
        if not a.recording or a.feedback:
            raise ValueError('Measurement requires recording, without feedback mode')
        result = measure(state, json.loads(a.selection.read_text()), a.recording)
        a.output.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return
    prompt = (
        'Observation-only grasp geometry diagnosis for the loose GPU card, after failed RGB-only '
        'closures and an open-in-place release. No grasp is verified. Choose up to6 visible '
        'solid surface pixels useful for assessing lateral centering/thickness: card shroud, '
        'opposing visible face, top, or visible finger pad. Do NOT require a center-top point '
        'if occluded; off-center visible patches are useful. Never invent the hidden opposite '
        'face. Identify what each sample actually shows and whether it constrains thickness '
        'or only one surface. Avoid empty gaps and depth edges. Use ORIGINAL640x360 integer '
        'pixels [u,v], origin upper-left. Code will measure depth; do not guess world positions. '
        'Return JSON observation_id, samples (list of {camera:left/right/wrist,pixel_uv:[u,v],'
        'surface:string}), missing_geometry, evidence. Empty list is allowed. This selects '
        'measurements only, not motion. Robot-only state: '+json.dumps(state))
    if a.feedback:
        feedback = json.loads(a.feedback.read_text())
        if feedback['observation_id'] != state['observation_id']:
            raise ValueError('Stale feedback')
        prompt = (
            'Review CURRENT RGB and measured surface geometry after failed RGB-only grasps. '
            'No motion is requested. The fingers have been released open; card capture is '
            'unverified. Explain whether sampled surfaces support lateral miscentering, '
            'insufficient depth, incorrect jaw orientation, or insufficient evidence. '
            'A sample label is the earlier model hypothesis, not semantic truth. Rejected '
            'samples supply no geometry. Nominal pinch offsets use hand axes, hand Y closing '
            'direction. One face is NOT thickness center; never prescribe direct motion by '
            'copying its offset. Return JSON observation_id, supported_findings, '
            'unsupported_claims, missing_measurements, next_observation. '
            'Robot state: '+json.dumps(state)+'\nDepth feedback: '+json.dumps(feedback))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((a.capture/f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': role}, {'type': 'image_url',
                        'image_url': {'url': 'data:image/png;base64,'+encoded}}])
    a.output.write_text(json.dumps([{'role': 'user', 'content': content}]))


if __name__ == '__main__':
    main()
