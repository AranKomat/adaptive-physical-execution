#!/usr/bin/env python3
"""Build one sensor-grounded bounded closure hypothesis; never execute motion."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from prepare_sensor_target_request import closeup_content, overview_content

from physical_exec.depth import surface_patch
from physical_exec.geometry import pose_matrix
from physical_exec.trace import write_json


def measure_samples(capture, selection):
    state = json.loads((capture/'state.json').read_text())
    if selection['observation_id'] != state['observation_id']:
        raise ValueError('Selection must match current capture')
    samples = selection['samples']
    if not isinstance(samples, list) or not 1 <= len(samples) <= 6:
        raise ValueError('Requires one to six declared sensor samples')
    hand = pose_matrix(state['hand_pose_world'])
    pinch = (hand @ np.array([0., 0., .1034, 1.]))[:3]
    rows = []
    for sample in samples:
        camera = sample['camera']
        if camera not in ('left', 'right', 'wrist'):
            raise ValueError('Invalid camera')
        if not isinstance(sample['surface_hypothesis'], str) or not sample['surface_hypothesis']:
            raise ValueError('Explicit operator surface hypothesis required')
        calibration = json.loads((capture/f'{camera}_calibration.json').read_text())
        if calibration['observation_id'] != state['observation_id']:
            raise ValueError('Stale calibration')
        depth = np.load(capture/f'{camera}_depth.npy', allow_pickle=False)
        row = {'operator_selection': sample}
        try:
            measurement = surface_patch(depth, calibration, sample['pixel_uv'])
            world = np.array(measurement['surface_point_world_m'])
            row.update(status='measured', measurement=measurement,
                       point_hand_m=(np.linalg.inv(hand) @ np.r_[world, 1.])[:3].tolist(),
                       nominal_pinch_minus_sample_world_m=(pinch-world).tolist())
        except ValueError as exc:
            row.update(status='rejected', reason=str(exc))
        rows.append(row)
    return state, {'observation_id': state['observation_id'], 'samples': rows,
                       'nominal_pinch_world_m': pinch.tolist(),
                       'limitation': 'Operator labels are visual hypotheses, not semantic truth. '
                       'Visible surface samples and nominal pinch offsets are not full finger '
                       'geometry, opposing contacts, clearance, force or grasp verification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--opening', type=float, required=True)
    parser.add_argument('--closeup-right', type=int, nargs=4)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not np.isfinite(args.opening) or not 0 <= args.opening < 1:
        raise ValueError('Invalid proposed closure aperture')
    state, feedback = measure_samples(args.capture, json.loads(args.selection.read_text()))
    proposal = {'observation_id': state['observation_id'], 'hand_pose_world': state['hand_pose_world'],
                    'gripper_open': args.opening, 'max_steps': 64, 'contact_tracking_guard': True,
                    'lift_authorized': False, 'automatic_retry': False}
    prompt = (
        'Assess ONE exploratory simulator closure proposal at the CURRENT open-hand pose. '
        'Earlier RGB-only review left pad/support ambiguity, so legal measured depth samples '
        'are supplied now. Do not assume their operator-selected semantic labels are correct. '
        'Use images to corroborate or reject those labels; rejected samples supply no geometry. '
        'The proposal holds the current hand pose and changes only normalized opening toward '
        'the declared setpoint over at most64 control actions at15Hz. It includes the existing '
        'per-action10mm/0.10rad tracking stop, with no automatic retry, lift or transit. '
        'These stops are NOT force/contact sensing. Simulator grasp assistance is ON. '
        'External clearance and unseen contact patches remain unknown; this is NOT strict '
        'benchmark/hardware authorization or certification. A close_candidate is a bounded '
        'contact hypothesis, not a guarantee that both exact inner pad patches are visible. '
        'Choose inspect/reposition if the next closure hypothesis remains unsupported, a '
        'surface is misidentified, or interference/misalignment is indicated. Never turn '
        'unknown space into certified free space or infer capture from arrival/opening. '
        'Consider whether measured support/finger separation helps the specific proposed '
        'closure, without treating a few surface samples as an exhaustive volume check. '
        'Return JSON observation_id, decision(close_candidate/reposition/inspect), '
        'opposing_contact_evidence, longitudinal_center_evidence, interference_evidence, '
        'measurement_label_assessment, uncertainty, expected_effect, stop_conditions. '
        '\nRobot-only state: '+json.dumps(state)+'\nProposal: '+json.dumps(proposal)+
        '\nCURRENT legal sensor feedback: '+json.dumps(feedback))
    content = [{'type': 'text', 'text': prompt}]
    for camera in ('left', 'right', 'wrist'):
        content.extend(overview_content(args.capture, camera))
    if args.closeup_right:
        content.extend(closeup_content(args.capture, 'right', args.closeup_right))
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output/'measurements.json', feedback)
    write_json(args.output/'proposal.json', proposal)
    write_json(args.output/'messages.json', [{'role': 'user', 'content': content}])
    print(json.dumps(feedback, indent=2))


if __name__ == '__main__':
    main()
