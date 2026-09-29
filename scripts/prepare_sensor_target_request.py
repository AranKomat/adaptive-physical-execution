#!/usr/bin/env python3
"""Build a bounded visual targeting request from an observation-only capture."""
import argparse
import base64
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stage', choices=['approach', 'grasp'], required=True)
    args = p.parse_args()
    state = json.loads((args.capture / 'state.json').read_text())
    prompt = (
        'Identify the loose graphics card standing beside the computer chassis, NOT cards inside it. '
        'We are planning a simulator-only top-down parallel-jaw grasp with RGB-D. '
        'Select one ORIGINAL 640x360-image integer pixel on a visible interior TOP surface of '
        'the loose card, near the middle of its length AND centered across its thickness. '
        'Do not choose the front face, support stand, metal end bracket, table, or empty gap. '
        'The pixel will be deprojected using measured depth; do NOT guess world coordinates. '
        'If the center is not visible or depth sampling would straddle an edge, say inspect. '
        'Consider all views; wrist may clip part of the object. '
        'Return only JSON with observation_id (copy supplied value), decision (target or inspect), '
        'camera (left, right or wrist), pixel_uv ([u,v] integers), evidence (string), uncertainty (string). '
        'Pixel origin is image upper-left, u rightward, v downward. '
        + ('This point is for an open-gripper standoff approach, NOT closure yet. ' if args.stage == 'approach'
           else 'This point will anchor grasp geometry: prioritize centering across both opposing '
                'faces, not merely choosing any visible top-edge point. We will inspect the target '
                'before commanding closure; do not assume prior grasp success. ')
        + '\nRobot-only state: ' + json.dumps(state))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((args.capture / f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': 'Current camera: ' + role},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role': 'user', 'content': content}]))


if __name__ == '__main__':
    main()
