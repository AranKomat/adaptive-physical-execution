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
    p.add_argument('--stage', choices=['approach', 'grasp', 'carry', 'alignment'], required=True)
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
    if args.stage == 'carry':
        prompt = (
            'Review these CURRENT simulator images after an attempted graphics-card grasp/lift. '
            'Do not infer capture from gripper aperture or the requested movement: decide from visible evidence. '
            'The task is to install the loose card into the computer chassis. We can next move the held '
            'card above the slot, WITHOUT descending into it, or inspect/stop. '
            'If the card is clearly held off its support and a destination is visible, choose carry_above_slot. '
            'Select one visible solid pixel near the CENTER of the held card\'s bottom PCIe connector edge '
            '(held_feature), and one solid surface pixel at the center of the matching motherboard PCIe '
            'socket/slot inside the chassis (slot_feature). Do not confuse the RAM sticks, stand or case wall '
            'with the slot. These are rough carry anchors, not precision insertion certification. '
            'Use original 640x360 integer pixel coordinates [u,v], upper-left origin. Depth will be measured '
            'at the selected pixels; never guess world coordinates. Each feature has camera (left/right/wrist) '
            'and pixel_uv. If a feature cannot be located reliably, choose inspect and explain what is missing. '
            'Return JSON with observation_id, decision (carry_above_slot/inspect/stop), held_feature, '
            'slot_feature, evidence, uncertainty. Features may be null for inspect/stop. '
            'No hidden object state, grasp status, collision certificate or force sensor is supplied. '
            '\nRobot-only state: ' + json.dumps(state))
    if args.stage == 'alignment':
        prompt = (
            'Review CURRENT RGB-D camera images after an elevated graphics-card carry. '
            'Determine whether the held card bottom PCIe connector and matching motherboard socket '
            'are actually visible and aligned. Do not assume the preceding carry chose the correct socket. '
            'Distinguish RAM sticks, heatsinks, case walls and card support from the PCIe socket. '
            'No object truth, grasp flag or known socket coordinates are available. '
            'Return JSON with observation_id, decision (features_visible/inspect/stop), '
            'held_feature and slot_feature (each camera left/right/wrist and pixel_uv [u,v], or null), '
            'alignment_evidence, uncertainty, and suggested_next_observation. '
            'Choose features_visible only if both matching features can be reliably identified. '
            'Use original 640x360 integer pixels, origin upper-left; never invent world coordinates. '
            'Selected pixels must lie on visible solid surfaces whose depth is meaningful, not gaps. '
            'State whether connector orientation can be checked, not merely center position. '
            'This review does NOT authorize insertion or descent. If occluded, explain which view '
            'is missing without presuming any unobserved space is clear. '
            '\nRobot-only state: ' + json.dumps(state))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((args.capture / f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': 'Current camera: ' + role},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role': 'user', 'content': content}]))


if __name__ == '__main__':
    main()
