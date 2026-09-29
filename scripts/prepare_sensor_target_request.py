#!/usr/bin/env python3
"""Build a bounded visual targeting request from an observation-only capture."""
import argparse
import base64
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.depth import surface_point, project_surface_memory


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stage', choices=['approach', 'grasp', 'carry', 'alignment', 'socket', 'socket_gap', 'held_feature', 'correspondence', 'inspection_motion', 'inspection_camera', 'feature_inventory', 'contact_recovery'], required=True)
    p.add_argument('--prior-socket-capture', type=Path)
    p.add_argument('--prior-socket-response', type=Path)
    p.add_argument('--prior-carry-capture', type=Path)
    p.add_argument('--prior-carry-response', type=Path)
    p.add_argument('--project-carry-anchor',action='store_true')
    p.add_argument('--contact-receipt',type=Path)
    args = p.parse_args()
    if args.project_carry_anchor and not (args.prior_carry_capture and args.prior_carry_response):
        raise ValueError('Projected carry anchor requires historical capture and response')
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
    if args.stage == 'correspondence':
        prompt = (
            'Inspect this retained simulator observation of a held graphics card near a motherboard. '
            'This is an offline correspondence review, NOT motion authorization. No evaluator result '
            'or object truth is supplied. Determine whether BOTH ends of the actual gold PCIe '
            'connector and BOTH corresponding ends of its destination socket can be identified. '
            'Do not substitute the whole card length, RAM slots, heatsink, or a socket housing center '
            'for mating features. End a must correspond to the bracket side and end b to the opposite '
            'side; if this association is uncertain, say so instead of assigning arbitrary endpoints. '
            'For each of connector and socket return end_a and end_b, each either null or '
            '{camera: left/right/wrist, pixel_uv: [u,v], surface: description}. Use ORIGINAL '
            '640x360 integer pixels with upper-left origin. These must be visible solid-surface '
            'pixels suitable for later measured depth, NOT guessed points in occluded space or gaps. '
            'Return only JSON: observation_id, decision (correspondence_visible/inspect/stop), '
            'connector, socket, key_visible (boolean), evidence, uncertainty, next_view. '
            'Choose correspondence_visible only when matching endpoints are actually visible. '
            'Describe in next_view the camera viewing direction needed to resolve missing evidence '
            'and whether the hand/card itself blocks it. Do not invent a calibrated camera position, '
            'world coordinates, seating depth, or clearance. One feature pixel alone does not '
            'establish center alignment or insertion success. '
            '\nRobot-only state: ' + json.dumps(state))
    if args.stage == 'socket_gap':
        prompt = (
            'Inspect the upper long PCIe socket below the CPU area in these CURRENT images. '
            'We previously localized a housing rail, but a single rail is not the insertion centerline. '
            'Determine whether TWO distinct solid rails on opposite sides of the SAME insertion gap '
            'can actually be identified. Do not select two lines on one rail, decorations, a heatsink, '
            'or two different sockets. Do not infer hidden geometry from generic PCIe expectations. '
            'Return only JSON: observation_id, decision (rails_visible/inspect), camera '
            '(left/right/wrist or null), samples, evidence, uncertainty, key_visible. '
            'samples is either [] or three entries spaced along the visible gap, each with '
            'rail_a_uv and rail_b_uv: ORIGINAL 640x360 integer [u,v], upper-left origin. '
            'Within each pair use the same longitudinal station. Select interior SOLID surface '
            'pixels, not the dark gap itself. Keep rail_a on the same physical side in all pairs. '
            'Depth will be sampled independently with a 3x3 neighborhood; report if the rails '
            'are too narrow to support that. Choose inspect if you cannot distinguish the two '
            'rails reliably. This observation-only test does NOT authorize movement, provide '
            'seating depth, or certify clearance. A midpoint between measured rail surfaces would '
            'only be an inferred centerline, not a directly observed gap surface. '
            '\nRobot-only state: ' + json.dumps(state))
    if args.stage == 'inspection_motion':
        calibrations = {role: json.loads((args.capture/f'{role}_calibration.json').read_text())
                        for role in ('left','right','wrist')}
        if any(c['observation_id'] != state['observation_id'] for c in calibrations.values()):
            raise ValueError('Inspection camera geometry is stale')
        prompt = (
            'The loose graphics card has been lifted, but the motherboard PCIe socket is '
            'not identifiable in the current views. Plan at most ONE bounded simulator-only '
            'inspection translation, or decline if no useful small motion is justified. '
            'This is NOT a carry toward a guessed socket or insertion. External cameras are '
            'fixed; wrist camera moves rigidly with the hand and held card. Therefore moving '
            'the hand does not change card-to-wrist-camera occlusion; explain which background '
            'region or external view would become more informative. Do not assume unseen space '
            'is free. No object pose, collision truth or force sensor is supplied. '
            'Allowed motion: keep hand orientation and gripper command unchanged, translate '
            'at most 0.05 m Euclidean norm in WORLD coordinates, dz >= 0 (no lowering). '
            'The bounded local controller, not GPT, executes and stops the movement. '
            'If these limits cannot produce an informative view, choose no_informative_motion. '
            'Do not suggest a move merely to comply. Return JSON: observation_id, decision '
            '(inspect_motion/no_informative_motion), delta_world_m ([dx,dy,dz] or null), '
            'expected_visible_region, geometric_reasoning, visible_risks, uncertainty. '
            'Motion remains exploratory with unknown clearance, not safety-certified. '
            '\nRobot-only state: '+json.dumps(state)+
            '\nCurrent sensor calibration: '+json.dumps(calibrations))
    if args.stage == 'inspection_camera':
        calibrations = {role: json.loads((args.capture/f'{role}_calibration.json').read_text())
                        for role in ('left','right','wrist')}
        if any(c['observation_id'] != state['observation_id'] for c in calibrations.values()):
            raise ValueError('Inspection camera geometry is stale')
        prompt = (
            'Choose ONE informative view of the held graphics card lower PCIe contact edge. '
            'The right camera is an explicitly controllable idealized simulator camera; left and '
            'wrist cameras remain fixed relative to their mounts. The arm and gripper will HOLD, '
            'not translate or rotate. Current right view shows the cooler side and does not expose '
            'the lower mating edge. Avoid another nearby cooler-side view that repeats this failure. '
            'Use current RGB, robot pose and measured camera calibration to choose a different '
            'line of sight. Do not use hidden object geometry or assume generic card dimensions. '
            'Return JSON: observation_id, decision (move_camera/hold), eye_world_m, gaze_world_m '
            '(three-number vectors or null), expected_visible_feature, evidence, uncertainty. '
            'Allowed eye bounds: x[0,1], y[-0.7,0.7], z[0.3,1.6] meters. A straight camera path '
            'over64 actions at15Hz must move at most0.512m, at most0.12m/s and turn at most '
            '0.35rad/s. Keep eye at least0.1m from gaze; avoid a vertical look-at singularity. '
            'A deterministic preflight will reject infeasible paths. This camera has no collision '
            'body; this is not a hardware clearance claim. Choose hold if no informative feasible '
            'view can be justified. Do not require the socket and connector in the same image. '
            '\nRobot-only state: '+json.dumps(state)+
            '\nCurrent legal sensor calibration: '+json.dumps(calibrations))
    content = [{'type': 'text', 'text': prompt}]
    if args.stage=='contact_recovery':
        if args.contact_receipt is None:
            raise ValueError('Contact recovery requires actual execution receipt')
        receipt=json.loads(args.contact_receipt.read_text())
        if receipt['resulting_observation_id']!=state['observation_id']:
            raise ValueError('Contact receipt is stale')
        if receipt.get('reason') not in ('local stage budget ended without arrival',
                                        'contact tracking guard stopped motion') or receipt.get('status')!='executed':
            raise ValueError('Recovery requires a confirmed nonarrival, not ambiguous execution')
        content=[{'type':'text','text':(
            'Choose one bounded simulator recovery after an exploratory downward surface approach '
            'failed its endpoint tracking check. Do not infer actual force or contact identity from '
            'tracking error alone. Review the current images for retention, tilt and obstruction. '
            'Options: lift_5cm (translate the hand vertically up 5cm with CURRENT measured attitude '
            'and previous gripper command unchanged; no lateral movement, rotation correction or '
            'release), or hold (no action). The local controller enforces a 64-action limit and '
            'existing hard stops. No insertion retry is available. Unknown external clearance '
            'remains exploratory, not certified safe. Prefer hold if visible entanglement or loss '
            'makes this specific lift inappropriate; do not select lift merely to comply. '
            'Return JSON: observation_id, decision (lift_5cm/hold), visible_retention, '
            'obstruction_evidence, expected_effect, uncertainty. No evaluator/hidden state is supplied. '
            '\nCurrent robot-only state: '+json.dumps(state)+'\nActual controller receipt: '+json.dumps(receipt))}]
    if args.stage == 'feature_inventory':
        content = [{'type': 'text', 'text': (
            'Localize visible mating features independently in these CURRENT simulator images. '
            'This is an observation-only inventory, NOT an alignment verdict or motion permission. '
            'The task is installing a held graphics card into a motherboard. For each of connector '
            '(actual lower PCIe contact edge, not card body/shroud) and socket '
            '(motherboard PCIe socket housing, not RAM, heatsink or case), report separately '
            'whether it is visible. One may be localized even if the other is hidden. '
            'A visible key/notch is NOT required for rough surface/axis localization: report key '
            'visibility independently. Do not infer hidden points from generic expectations. '
            'Choose two separated interior solid-surface pixels along each visible feature to '
            'estimate a rough axis; if only one point is reliable, return that point only. '
            'Do not treat these points as exact mating endpoints or the gap centerline. '
            'Each feature: status (axis_visible/point_visible/occluded/uncertain), samples '
            '(list of {camera: left/right/wrist, pixel_uv: [u,v], surface: description}), '
            'key_visible (boolean), evidence, uncertainty. Use ORIGINAL 640x360 integer pixels, '
            'upper-left origin. Depth will be measured independently; do not invent world poses. '
            'Return JSON with observation_id, connector, socket, and next_view describing only '
            'the view needed for missing features. Never call an empty gap a solid surface. '
            'Unseen clearance and insertion alignment remain unknown regardless of localization. '
            '\nRobot-only state: '+json.dumps(state))}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((args.capture / f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': 'Current camera: ' + role},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}])
    if args.prior_carry_capture or args.prior_carry_response:
        if args.stage not in ('feature_inventory','correspondence','inspection_camera') or not (args.prior_carry_capture and args.prior_carry_response):
            raise ValueError('carry history requires feature inventory/correspondence/camera inspection and both prior inputs')
        old_state = json.loads((args.prior_carry_capture/'state.json').read_text())
        old_response = json.loads(args.prior_carry_response.read_text())
        old_episode, old_seq = old_state['observation_id'].rsplit(':', 1)
        episode, seq = state['observation_id'].rsplit(':', 1)
        if (old_episode != episode or int(old_seq) >= int(seq)
                or old_response['observation_id'] != old_state['observation_id']
                or old_response['decision'] != 'carry_above_slot'):
            raise ValueError('carry history must be an earlier selection in the same episode')
        role = old_response['slot_feature']['camera']
        if role not in ('left','right','wrist'):
            raise ValueError('invalid historical camera')
        if args.project_carry_anchor:
            old_calibration = json.loads((args.prior_carry_capture/f'{role}_calibration.json').read_text())
            if old_calibration['observation_id']!=old_state['observation_id']:
                raise ValueError('Historical calibration is stale')
            point = surface_point(np.load(args.prior_carry_capture/f'{role}_depth.npy',allow_pickle=False),
                old_calibration,old_response['slot_feature']['pixel_uv'],radius=1,max_spread_m=.01)
            projections = {}
            for current_role in ('left','right','wrist'):
                c = json.loads((args.capture/f'{current_role}_calibration.json').read_text())
                if c['observation_id']!=state['observation_id']:
                    raise ValueError('Current calibration is stale')
                projections[current_role] = project_surface_memory(point,c,
                    np.load(args.capture/f'{current_role}_depth.npy',allow_pickle=False))
            content.append({'type':'text','text':(
                'PROJECTED HISTORICAL SENSOR ANCHOR, not a simulator object pose: the earlier '
                'socket surface sample is projected into each CURRENT camera using calibration. '
                'Use it to resolve which slot was previously selected, not to presume it was correct. '
                'A depth-consistent point supplies a candidate visible location, not verified identity, '
                'endpoints or clearance. An inconsistent point may be occluded or the surface may '
                'have moved; do not treat it as a current surface. Explain any contradiction between '
                'your visual selection and this anchor. '+json.dumps(projections))})
        encoded = base64.b64encode((args.prior_carry_capture/f'{role}.png').read_bytes()).decode()
        content.extend([
            {'type':'text','text':(
                'HISTORICAL carry target, NOT a current observation or certified correct socket. '
                'There may be several similar PCIe sockets. Track the SAME selected socket into '
                'the current view; do not silently switch to a more visible neighboring slot. '
                'If it is cropped or occluded, report that. If the old identification was wrong, '
                'explain rather than preserving it blindly. Return current-image samples only, '
                'plus target_identity_assessment. History is not clearance or insertion approval. '
                +json.dumps(old_response))},
            {'type':'image_url','image_url':{'url':'data:image/png;base64,'+encoded}}])
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
