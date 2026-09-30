#!/usr/bin/env python3
"""Prepare a scene-level advisory review with explicit historical sensor evidence."""
import argparse
import base64
import json
from pathlib import Path


def build_messages(capture, historical_capture, measurements, inventory, episode_note):
    if not isinstance(episode_note, str) or not episode_note.strip() or len(episode_note) > 2000:
        raise ValueError('Explicit bounded operator episode note required')
    state = json.loads((capture/'state.json').read_text())
    old = json.loads((historical_capture/'state.json').read_text())
    current_episode, current_step = state['observation_id'].rsplit(':', 1)
    old_episode, old_step = old['observation_id'].rsplit(':', 1)
    if (old_episode != current_episode or int(old_step) >= int(current_step)
            or measurements['observation_id'] != old['observation_id']
            or inventory['observation_id'] != old['observation_id']):
        raise ValueError('Historical evidence must match an earlier same-episode capture')
    content = [{'type': 'text', 'text': (
        'Task: install the held graphics card into the computer PCIe slot. '
        'Assess the whole current manipulation situation and propose the next meaningful '
        'physical stage, not another generic rail-wording experiment. This is advisory '
        'planning only: no command is automatically executed. '
        'Current images, robot FK, and earlier legal RGB-D feature samples are supplied. '
        'Historical samples are NOT current poses, endpoint correspondence or clearance. '
        'The sampled socket rim is not a centerline. Do not assume two opposing rails '
        'have been established. Consider whether such detail is '
        'actually needed for the NEXT noncontact stage, rather than treating insertion '
        'precision as mandatory for every approach. Conversely, do not claim the rim is '
        'the gap or that hidden space is clear. No hidden object state, force feedback, '
        'collision truth, seating depth or evaluator is available. '
        'Recommend one bounded stage: alignment, closer approach, contact proposal, '
        'inspection or hold. If recommending physical movement, limit the proposed hand '
        'translation to5cm and rotation to0.15rad, preserving gripper aperture. These are '
        'proposal limits, not permission or proof of safety. Explain useful progress and '
        'what evidence would falsify the proposal. Do not invent target coordinates. '
        'You may specify a relative delta in world coordinates only if justified by '
        'the supplied geometry; label estimates and assumptions. Otherwise identify '
        'up to four CURRENT visible solid-surface anchors with camera and original '
        '640x360 integer pixel_uv [u,v], origin upper-left. Distinguish a rough socket '
        'reference from a contact centerline. Identify possible target misassociation '
        'instead of blindly preserving an earlier selection. '
        'Return JSON observation_id, visible_state, next_stage, proposed_delta_world_m '
        '(or null), proposed_rotation_world_rad (or null), anchors, assumptions, '
        'expected_effect, stop_conditions, remaining_stages, uncertainty. Keep under '
        '450words with at most three remaining stages and three stop conditions. '
        '\nOPERATOR episode note (not sensor evidence): '+episode_note+
        '\nCURRENT robot state: '+json.dumps(state)+
        '\nHISTORICAL feature inventory: '+json.dumps(inventory)+
        '\nHISTORICAL measured samples: '+json.dumps(measurements))}]
    for source, roles, label in ((capture, ('left', 'right', 'wrist'), 'CURRENT'),
                                 (historical_capture, ('right',), 'HISTORICAL')):
        for role in roles:
            encoded = base64.b64encode((source/f'{role}.png').read_bytes()).decode()
            content.extend([{'type': 'text', 'text': f'{label} camera {role}'},
                            {'type': 'image_url', 'image_url': {
                                'url': 'data:image/png;base64,'+encoded}}])
    return [{'role': 'user', 'content': content}]


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--historical-capture', type=Path, required=True)
    p.add_argument('--measurements', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--episode-note', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    messages = build_messages(a.capture, a.historical_capture,
                              json.loads(a.measurements.read_text()),
                              json.loads(a.inventory.read_text()), a.episode_note)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as stream:
        json.dump(messages, stream)
