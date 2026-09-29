#!/usr/bin/env python3
"""Observation-only grasp geometry review; never includes later outcome or evaluator truth."""
import argparse
import base64
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--correction', type=Path, required=True)
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stages = json.loads((args.correction/'declared_sequence.json').read_text())
    if not 0 <= args.index < len(stages) or stages[args.index]['name'] != 'descend':
        raise ValueError('Review must reference a descent endpoint')
    state = json.loads((args.correction/f'{args.index:02d}_observation.json').read_text())
    prompt = (
        'Review ONLY this current pre-closure robot observation. The task is to grasp the '
        'loose upright graphics card outside the case with parallel fingers, then lift it. '
        'A prior controller reached its requested pose, but that does NOT prove good grasp '
        'geometry. Determine whether the open fingers visibly straddle opposing card faces, '
        'whether the grasp is reasonably centered along the card, and whether either finger '
        'is on a bracket, support, protrusion or wrong edge. Distinguish unknown from observed '
        'misalignment. No segmentation, object state, force or clearance oracle is supplied. '
        'Return JSON with observation_id, decision (close_candidate/reposition/inspect), '
        'opposing_contact_evidence, longitudinal_center_evidence, interference_evidence, '
        'uncertainty, next_observation_or_correction. A close_candidate is a visual hypothesis, '
        'not certified collision freedom or verified grasp. If evidence is insufficient, '
        'choose inspect rather than assuming the requested pose is correct. '
        'Use original 640x360 pixel coordinates when referring to image locations; never '
        'invent world object coordinates. Robot-only state: '+json.dumps(state))
    content = [{'type':'text','text':prompt}]
    for role in ('left','right','wrist'):
        pixels = (args.correction/f'{args.index:02d}_{role}.png').read_bytes()
        content.extend([{'type':'text','text':role}, {'type':'image_url',
                        'image_url':{'url':'data:image/png;base64,'+base64.b64encode(pixels).decode()}}])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role':'user','content':content}]))


if __name__ == '__main__':
    main()
