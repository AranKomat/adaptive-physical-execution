#!/usr/bin/env python3
"""One reviewed simulator release at measured pose; no reset, lift or retry."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.transport import LocalClient, decode_observation, decode_result
from physical_exec.trace import write_json
from physical_exec.imaging import png_bytes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url', required=True)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    review = json.loads(a.review.read_text())
    if review['decision'] != 'open_in_place':
        raise ValueError('Review did not select release')
    a.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(a.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        if (meta.get('real_hardware_supported') is not False or
                not meta.get('contact_tracking_guard_enabled')):
            raise ValueError('Requires guarded simulator')
        obs = decode_observation(client.call('/observe'))
        if obs.key != review['observation_id']:
            raise ValueError('Review is stale; no execution')
        request = dict(observation_id=obs.key, hand_pose_world=obs.eef_pose.tolist(),
            gripper_open=1., max_steps=30, contact_tracking_guard=True,
            motion_profile='conservative',
            target_source='Operator bounded release selected by current visual review; unknown clearance')
        write_json(a.output/'request.json', request)
        result = decode_result(client.call('/local-stage',
            {'command_id': uuid4().hex, 'action': request}, mutating=True))
        write_json(a.output/'receipt.json', result.receipt.to_dict())
        write_json(a.output/'state.json', result.observation.public_state())
        for role, im in result.observation.images.items():
            (a.output/f'{role}.png').write_bytes(png_bytes(im))
        print(json.dumps(result.receipt.to_dict(), indent=2))
    finally:
        client.close()


if __name__ == '__main__':
    main()
