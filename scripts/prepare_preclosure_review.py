#!/usr/bin/env python3
"""Observation-only grasp geometry review; never includes later outcome or evaluator truth."""
import argparse
import json
from pathlib import Path

from prepare_sensor_target_request import closeup_image_content, overview_image_content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--correction', type=Path)
    source.add_argument('--inspection-probe', type=Path,
                        help='Actual completed camera hold at an existing open-hand preclosure pose')
    parser.add_argument('--index', type=int)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-object', choices=['graphics_card','ram_module'], default='graphics_card')
    parser.add_argument('--history-capture', type=Path)
    parser.add_argument('--history-plan', type=Path)
    parser.add_argument('--current-projections', type=Path)
    parser.add_argument('--closeup-right', nargs=4, type=int,
                        help='Current original-frame crop bounds; not an enhanced/generated image')
    args = parser.parse_args()
    if args.inspection_probe:
        if args.index is not None:
            raise ValueError('Inspection probe has no correction stage index')
        directory, prefix = args.inspection_probe, 'after'
        state = json.loads((directory/'after.json').read_text())
        receipt = json.loads((directory/'receipt.json').read_text())
        request = json.loads((directory/'request.json').read_text())['action']
        if (receipt['resulting_observation_id'] != state['observation_id']
                or receipt['observation_id'] != request['observation_id']
                or receipt['reason'] != 'local stage arrived'
                or request.get('gripper_open', 0) < .95
                or 'camera_eye_world' not in request):
            raise ValueError('Requires completed open-hand camera hold with matching receipt')
    else:
        stages = json.loads((args.correction/'declared_sequence.json').read_text())
        if (args.index is None or not 0 <= args.index < len(stages)
                or stages[args.index]['name'] not in ('descend','preclosure')):
            raise ValueError('Review must reference a descent endpoint')
        directory, prefix = args.correction, f'{args.index:02d}'
        state = json.loads((directory/f'{prefix}_observation.json').read_text())
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
        'Use ORIGINAL sensor pixel coordinates, with the per-image mapping below, '
        'when referring to image locations; never '
        'invent world object coordinates. Robot-only state: '+json.dumps(state))
    content = [{'type':'text','text':prompt}]
    if args.target_object == 'ram_module':
        prompt = prompt.replace('loose upright graphics card', 'loose upright RAM module')
        prompt = prompt.replace('opposing card faces', 'opposing module housing faces')
        prompt = prompt.replace('along the card', 'along the module')
        prompt += (' Proposed next stage, ONLY if supported: close parallel jaws toward nominal4mm '
                   'total aperture (open fraction0.05), holding CURRENT hand pose for at most64 '
                   'actions at15Hz, with per-action10mm/.10rad ramp tracking stop. No lift/retry. '
                   'The requested aperture is a setpoint, not measured thickness or force control. '
                   'The native simulator grasp assistance is enabled; do not infer grasp from it. '
                   'The upper colored strip is not automatically a structural gripping surface. '
                   'Evaluate visible finger placement relative to housing AND the gray support. '
                   'Unknown clearance stays exploratory, not certified.')
        content = [{'type':'text','text':prompt}]
    for role in ('left','right','wrist'):
        content.extend(overview_image_content(
            directory/f'{prefix}_{role}.png', 'CURRENT '+role))
    if args.closeup_right:
        content.extend(closeup_image_content(directory/f'{prefix}_right.png',
                                             'CURRENT right', args.closeup_right))
    if any((args.history_capture,args.history_plan,args.current_projections)):
        if not all((args.history_capture,args.history_plan,args.current_projections)):
            raise ValueError('History review requires capture, plan and current projections')
        old = json.loads((args.history_capture/'state.json').read_text())
        plan = json.loads(args.history_plan.read_text())
        projections = json.loads(args.current_projections.read_text())
        episode, step = state['observation_id'].rsplit(':',1)
        old_episode, old_step = old['observation_id'].rsplit(':',1)
        if (episode != old_episode or int(old_step) >= int(step)
                or plan['observation_id'] != old['observation_id']
                or projections['observation_id'] != state['observation_id']):
            raise ValueError('History/projections do not belong to this current observation')
        content.extend([{'type':'text','text':
            'Additional HISTORICAL sensor evidence, not current clearance: before approach, '
            'operator-marked center and axis on the module top were visible. Current calibrated '
            'depth comparisons and robot-nominal pinch offset follow. Use them to assess centering '
            'and identity despite clipping; do not equate nominal geometry with opposing-contact '
            'or collision proof. Outside-image/inconsistent samples are NOT validated historical '
            'points. Reassess with this additional evidence; approval is not expected or required. '
            +json.dumps({'historical_plan':plan,'current_geometry':projections})}])
        content.extend(overview_image_content(args.history_capture/'wrist.png', 'HISTORICAL wrist'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([{'role':'user','content':content}]))


if __name__ == '__main__':
    main()
