#!/usr/bin/env python3
"""Build an observation-only before/after lift review, without target or evaluator answers."""
import argparse
import base64
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--correction', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stages = json.loads((args.correction/'declared_sequence.json').read_text())
    close = next(i for i, stage in enumerate(stages) if stage['name'] == 'close')
    lift = len(stages)-1
    if stages[lift]['name'] != 'short_lift':
        raise ValueError('Expected a completed short-lift sequence')
    content = [{'type': 'text', 'text': (
        'Assess the loose graphics card from these actual simulator images before closure, '
        'after closure and after an attempted short lift. Do not assume that moving the hand '
        'means the card followed, or that a closed gripper proves capture. Distinguish full '
        'lift clear of its support from tilting one end while the other remains supported. '
        'Return JSON: decision (clear_lift/partial_contact/no_capture/uncertain), '
        'card_motion_evidence, support_clearance_evidence, grasp_stability_evidence, '
        'uncertainty. No motion is authorized by this review; no hidden state is supplied.')}]
    for label, index in [('before_closure',close-1), ('after_closure',close), ('after_lift',lift)]:
        state = json.loads((args.correction/f'{index:02d}_observation.json').read_text())
        content.append({'type':'text','text':label+' '+state['observation_id']})
        for role in ('left', 'wrist'):
            encoded = base64.b64encode((args.correction/f'{index:02d}_{role}.png').read_bytes()).decode()
            content.extend([{'type':'text','text':role}, {'type':'image_url',
                            'image_url':{'url':'data:image/png;base64,'+encoded}}])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role':'user','content':content}]))


if __name__ == '__main__':
    main()
