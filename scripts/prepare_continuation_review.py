#!/usr/bin/env python3
"""Prepare an advisory scene-level review from public recovery observations only."""
import argparse
import base64
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recovery', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    before = json.loads((args.recovery/'before.json').read_text())
    after = json.loads((args.recovery/'after.json').read_text())
    receipt = json.loads((args.recovery/'receipt.json').read_text())
    if (before['episode_id'] != after['episode_id']
            or before['step'] >= after['step']
            or receipt['observation_id'] != before['observation_id']
            or receipt['resulting_observation_id'] != after['observation_id']):
        raise ValueError('Recovery provenance mismatch')
    content = [{'type': 'text', 'text': (
        'Task: Install the loose graphics card into the computer case\'s PCIe slot. '
        'Use visual feedback to align and seat it. We attempted a downward surface '
        'approach, observed nonarrival and tilt, and withdrew vertically 5cm while '
        'preserving measured hand attitude and grip. The supplied receipt is the '
        'withdrawal, not insertion. No successful assembly is presumed. '
        'Assess the whole manipulation situation, not just the slot center. '
        'Propose the next useful stage and a short remaining plan. You may recommend '
        'reorientation, repositioning, inspection, or stopping. Do not simply repeat '
        'descent. Identify visible evidence supporting the proposed interaction, '
        'distinguish hypotheses from observations, and say what would falsify it. '
        'We have RGB plus independently sampleable aligned depth and robot FK, '
        'but no force sensor, hidden geometry, object poses or evaluator feedback. '
        'Do not invent world coordinates, obstacle clearance, or unseen features. '
        'If geometry is needed, name visible solid-surface anchors using ORIGINAL '
        '640x360 integer pixel_uv [u,v], origin top-left, camera left/right/wrist. '
        'No code is requested. This is advisory planning only; no motion is '
        'automatically dispatched. Use up to three meaningful remaining stages, '
        'not a long list of tiny robot corrections. Return JSON with observation_id, '
        'visible_state, failure_hypotheses, next_stage, anchors, remaining_stages, '
        'stop_conditions, missing_evidence, uncertainty. Keep the ENTIRE response '
        'under 450 words: at most two failure hypotheses, four anchors, three '
        'stages, and three stop conditions. Use short strings, not nested essays. '
        '\nCurrent public robot state: '+json.dumps(after)+
        '\nWithdrawal receipt: '+json.dumps(receipt))}]
    for prefix, label in [('before', 'HISTORICAL before withdrawal'),
                          ('after', 'CURRENT after withdrawal')]:
        for role in ('left', 'right', 'wrist'):
            data = base64.b64encode((args.recovery/f'{prefix}_{role}.png').read_bytes()).decode()
            content.extend([{'type': 'text', 'text': label+' camera '+role},
                            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,'+data}}])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump([{'role': 'user', 'content': content}], stream)


if __name__ == '__main__':
    main()
