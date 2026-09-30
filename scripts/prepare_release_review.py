#!/usr/bin/env python3
"""Observation-only review of open-in-place recovery after a closure guard stop."""
import argparse
import base64
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--retreat-after-release', action='store_true')
    a = p.parse_args()
    state = json.loads((a.capture/'state.json').read_text())
    if a.retreat_after_release:
        receipt = json.loads((a.run/'receipt.json').read_text())
        if receipt['reason'] != 'local stage arrived' or state['gripper_open_fraction'] < .99:
            raise ValueError('Retreat review requires arrived open release')
    else:
        rows = [json.loads(s) for s in (a.run/'events.jsonl').read_text().splitlines()]
        receipt = [r['data'] for r in rows if r['kind'] == 'execution_receipt'][-1]
    if receipt['resulting_observation_id'] != state['observation_id']:
        raise ValueError('Review capture and receipt must match')
    prompt = (
        'Review a simulator-only recovery after stationary gripper closure exceeded the '
        'unchanged hand tracking guard. No grasp is verified. Do NOT recommend lifting '
        'or repeating closure. Evaluate only OPEN IN PLACE at the CURRENT measured hand '
        'pose (not the old commanded pose), up to 30 local control actions, same guard, '
        'no translation/rotation target change. This may release a constrained object; '
        'assess whether the images show it supported or visibly entangled. Unknown '
        'clearance remains unknown. Return JSON observation_id, decision '
        '(open_in_place/hold), evidence, risks, expected_effect. Choose hold if evidence '
        'does not support this bounded release. This is a proposal review, not proof '
        'of safety, grasp or permission for subsequent motion. Robot state: '
        + json.dumps(state) + '\nExecution receipt: ' + json.dumps(receipt))
    if a.retreat_after_release:
        prompt = (
            'Review a simulator-only inspection retreat after an open-in-place release. '
            'No grasp is verified. Assess only a 5cm world-Z upward hand retreat, '
            'gripper held OPEN, unchanged lateral position/orientation, at most60 '
            'conservative local actions with unchanged tracking guard. It is NOT '
            'a held-object lift. The purpose is to expose the card top for RGB-D '
            'targeting. Consider visible entanglement/obstruction or possible card '
            'motion; unknown clearance is not certified free. Return JSON '
            'observation_id, decision (retreat_up_5cm/hold), evidence, risks, '
            'expected_effect. Choose hold if this specific retreat is unsupported. '
            'No other action is authorized by this review. Current robot state: '
            + json.dumps(state) + '\nRelease receipt: ' + json.dumps(receipt))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((a.capture/f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': role}, {'type': 'image_url',
            'image_url': {'url': 'data:image/png;base64,'+encoded}}])
    a.output.write_text(json.dumps([{'role': 'user', 'content': content}]))


if __name__ == '__main__':
    main()
