#!/usr/bin/env python3
"""Review one explicitly bounded exploratory approach using current measured features."""
import argparse
import base64
import json
from pathlib import Path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--measurements', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
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
    content = [{'type': 'text', 'text': prompt}]
    for role in ('left', 'right', 'wrist'):
        encoded = base64.b64encode((a.capture/f'{role}.png').read_bytes()).decode()
        content.extend([{'type': 'text', 'text': 'CURRENT '+role},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,'+encoded}}])
    with a.output.open('x') as stream:
        json.dump([{'role': 'user', 'content': content}], stream)
