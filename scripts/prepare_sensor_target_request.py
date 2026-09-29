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
    p.add_argument('--stage', choices=['approach', 'grasp', 'carry', 'alignment', 'socket', 'held_feature'], required=True)
    p.add_argument('--prior-socket-capture', type=Path)
    p.add_argument('--prior-socket-response', type=Path)
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
            'Review CURRENT RGB camera images after an elevated graphics-card carry. '
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
    if args.stage == 'socket':
        prompt = (
            'Before grasping the loose graphics card, identify its destination motherboard PCIe '
            'socket in the CURRENT RGB images. Do not choose the loose card support, RAM sticks '
            'or RAM slots, heatsink fins, case rim, or the large black case fan. '
            'This is a visual localization test, NOT permission to move. '
            'Choose localized only if you can distinguish the destination socket from distractors. '
            'Select center, end_a, end_b: three ORIGINAL 640x360 integer pixels on the visible '
            'solid socket housing, spanning its LONG axis. Avoid empty socket gaps and background. '
            'Each feature is {camera: left/right/wrist, pixel_uv: [u,v]}. '
            'Pixel origin is upper-left; u increases right, v down. '
            'Measured depth exists separately and will be sampled after your selection; it is not '
            'included here. Never invent world coordinates or claim depth certification. '
            'Return JSON with observation_id, decision (localized/inspect), center, end_a, end_b, '
            'evidence, uncertainty. Features may be null when inspect is required. '
            'Explicitly distinguish seeing a socket housing/axis from seeing its insertion gap '
            'or key: do not require a visible key for rough localization, but report its absence. '
            'Do not infer that any occluded space is clear. '
            '\nRobot-only state: ' + json.dumps(state))
    if args.stage == 'held_feature':
        prompt = (
            'Locate the held graphics card\'s LOWER PCIe contact/connector edge in CURRENT images. '
            'The camera has moved to inspect the PCB side. We need one solid-surface pixel near the '
            'middle of that lower mating edge, not the upper grasp edge, bracket, heatsink or background. '
            'Use original 640x360 integer pixel_uv [u,v], upper-left origin. Depth will be measured '
            'after selection; do not invent world coordinates or claim clearance. '
            'This is feature localization only, not insertion authorization. You do not need to see '
            'the socket or resolve a key notch to locate a visible contact edge. '
            'Return JSON with observation_id, decision (target/inspect), camera (left/right/wrist), '
            'pixel_uv, evidence, uncertainty. If the lower mating edge is not reliably identifiable, '
            'choose inspect and use null for camera and pixel_uv. '
            '\nRobot-only state: ' + json.dumps(state))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((args.capture / f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': 'Current camera: ' + role},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}])
    if args.prior_socket_capture or args.prior_socket_response:
        if args.stage != 'alignment' or not (args.prior_socket_capture and args.prior_socket_response):
            raise ValueError('historical socket context requires alignment and both prior inputs')
        old_state = json.loads((args.prior_socket_capture/'state.json').read_text())
        old_response = json.loads(args.prior_socket_response.read_text())
        old_episode, old_seq = old_state['observation_id'].rsplit(':', 1)
        episode, seq = state['observation_id'].rsplit(':', 1)
        if (old_episode != episode or int(old_seq) >= int(seq)
                or old_response['observation_id'] != old_state['observation_id']
                or old_response['decision'] != 'localized'):
            raise ValueError('historical socket evidence must be an earlier localized view in this episode')
        role = old_response['center']['camera']
        if role not in ('left', 'right', 'wrist'):
            raise ValueError('invalid historical camera')
        encoded = base64.b64encode((args.prior_socket_capture/f'{role}.png').read_bytes()).decode()
        content.extend([
            {'type': 'text', 'text': (
                'HISTORICAL evidence, NOT a current view or clearance certificate. '
                'An earlier pre-grasp review localized a candidate socket housing in this same episode. '
                'Reconcile this evidence with the current views; do not describe it as never observed. '
                'Keep the current decision schema, and add historical_assessment explaining what '
                'this memory resolves, what may have changed, and what current evidence remains missing. '
                'Localization was coarse, not verified gap/key geometry. Memory alone does not '
                'authorize descent, prove absence of slip, or establish current free space. '
                + json.dumps(old_response))},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}},
        ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role': 'user', 'content': content}]))


if __name__ == '__main__':
    main()
