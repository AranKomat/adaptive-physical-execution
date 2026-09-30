#!/usr/bin/env python3
"""Review one explicitly bounded exploratory approach using current measured features."""
import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from prepare_sensor_target_request import closeup_content, overview_content

from physical_exec.carry import standoff_stages

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--measurements', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--contact-hypothesis', action='store_true',
                   help='Review the existing bounded vertical plane-contact compiler, not insertion')
    p.add_argument('--closeup-right', type=int, nargs=4,
                   help='Current sensor crop in original pixel coordinates')
    a = p.parse_args()
    state = json.loads((a.capture/'state.json').read_text())
    measured = json.loads(a.measurements.read_text())
    if measured['observation_id'] != state['observation_id']:
        raise ValueError('Current depth measurements required')
    prompt = (
        'Task: install the held graphics card. Review ONE simulator-only coarse approach, '
        'not insertion: lower the current measured hand pose vertically4cm, preserve '
        'lateral position, attitude and current aperture0.3, at most64actions at15Hz. '
        'Native grasp assistance is ON. A deterministic compiler requires two current '
        '3x3-qualified samples per feature, at least8cm nominal sampled separation AFTER '
        'the move, rough horizontal axes within25degrees and transverse sample-line '
        'offset at most4cm. These conditions are NOT full-object collision clearance. '
        'Per-action tracking stops remain unchanged. No force sensor, hidden object '
        'geometry or evaluator is supplied. The sample points are NOT corresponding '
        'endpoints; the socket rim is NOT a gap centerline. No contact, lateral correction '
        'or release is proposed. Decide whether these CURRENT images and measurements '
        'support this bounded closer approach. Do not require insertion precision or '
        'two opposing rails for this noncontact proposal, but decline if visible '
        'interference, slip, target mismatch or inadequate evidence makes it unsupported. '
        'Return JSON observation_id, decision (approve_coarse_approach/inspect/stop), '
        'descent_m (0.04 if approved, otherwise null), evidence, uncertainty. '
        'Explicitly retain unknown external clearance. '
        '\nCurrent robot state: '+json.dumps(state)+
        '\nCurrent legal RGB-D samples: '+json.dumps(measured))
    if a.contact_hypothesis:
        stages = standoff_stages(measured, state['observation_id'],
                                state['hand_pose_world'], .3, contact=True)
        for stage in stages:
            stage['contact_tracking_guard'] = True
        prompt = (
            'Task: install the held graphics card. Review ONE exploratory simulator '
            'vertical PLANE-CONTACT hypothesis compiled below, not verified keyed insertion. '
            'The proposal lowers the current measured hand pose until the lowest sampled '
            'gold surface reaches the highest sampled socket-rim plane. At most8cm descent, '
            'at most two64-action segments at15Hz, continuous intermediate waypoint, final '
            'settling only. Preserve measured attitude, lateral position and aperture0.3. '
            'Native grasp assistance is ON. External swept clearance is UNKNOWN. '
            'Per-action10mm/0.10rad tracking stops remain unchanged, but are NOT force sensing '
            'or collision certification. No object poses, collision truth or evaluator are supplied. '
            'Gold/rim samples are surface references, not gap centerline or seating depth. '
            'The previous same-socket RGB review identified two rails and a possible key. '
            'Raw optical depth at sampled dark-gap pixels returned essentially rim-height; '
            'no measurable recess was established. Do not presume a physical keyed cavity. '
            'There is NO lateral correction, further grip closure, additional seating push, '
            'automatic retry or release in this proposal. A contact attempt may stop without '
            'arrival and will be reviewed independently, not counted as installation. '
            'Decide whether current visual/metric evidence supports this bounded contact '
            'experiment. Choose inspect/stop for visible misalignment, interference, slip, '
            'target mismatch or inadequate evidence. Do not demand a strict clearance '
            'certificate for this explicitly exploratory test, but retain all unknowns. '
            'Return JSON observation_id, decision (approve_contact_hypothesis/inspect/stop), '
            'evidence, uncertainty, expected_effect, stop_conditions. '
            '\nCurrent robot state: '+json.dumps(state)+
            '\nCURRENT surface measurements: '+json.dumps(measured)+
            '\nExact bounded stages: '+json.dumps(stages))
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        if a.contact_hypothesis:
            content.extend(overview_content(a.capture, role))
        else:
            encoded = base64.b64encode((a.capture/f'{role}.png').read_bytes()).decode()
            content.extend([{'type': 'text', 'text': 'CURRENT '+role},
                            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,'+encoded}}])
    if a.closeup_right:
        content.extend(closeup_content(a.capture, 'right', a.closeup_right))
    with a.output.open('x') as stream:
        json.dump([{'role': 'user', 'content': content}], stream)
