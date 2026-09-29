#!/usr/bin/env python3
"""Operator-defined same-episode correction using a fresh sensor-target plan, not autonomous recovery."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.geometry import pose_error, quat_mul, rotvec_to_quat
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    surface = np.asarray(plan['measured_surface']['surface_point_world_m'], dtype=float)
    if surface.shape != (3,) or not np.isfinite(surface).all():
        raise ValueError('Invalid measured surface')
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        metadata = client.call('/metadata')
        if not metadata.get('local_stages_enabled') or metadata.get('real_hardware_supported') is not False:
            raise ValueError('Requires opt-in simulator')
        obs = decode_observation(client.call('/observe'))
        if obs.key != plan['observation_id']:
            raise ValueError('Target plan is not current; no automatic reset or retry')
        write_json(args.output/'initial.json', obs.public_state())
        write_json(args.output/'source_plan.json', plan)
        retract = obs.eef_pose.copy()
        retract[2] += .05
        top = np.array([0., 0., 1., 0.])
        hand = surface + [0, 0, .1034-.015]
        endpoints = [('open_retract', retract, 1.),
                     ('top_down', np.r_[retract[:3], top], 1.),
                     ('standoff', np.r_[surface+[0,0,.22], top], 1.),
                     ('descend', np.r_[hand, top], 1.),
                     ('close', np.r_[hand, top], .3),
                     ('short_lift', np.r_[hand+[0,0,.05], top], .3)]
        # Predeclare the entire bounded sequence before the first mutation.
        stages = []
        start = obs.eef_pose.copy()
        for name, target, opening in endpoints:
            error = pose_error(start, target)
            n = max(1, math.ceil(np.linalg.norm(error[:3])/.06),
                    math.ceil(np.linalg.norm(error[3:])/.25))
            for i in range(1, n+1):
                pose = np.r_[start[:3]+error[:3]*i/n,
                             quat_mul(rotvec_to_quat(error[3:]*i/n), start[3:])]
                stages.append(dict(name=name, hand_pose_world=pose.tolist(), gripper_open=opening))
            start = target.copy()
        if len(stages) > 16:
            raise ValueError('Correction exceeds 16-stage/1024-action limit')
        write_json(args.output/'declared_sequence.json', stages)
        for index, stage in enumerate(stages):
            request = {key: stage[key] for key in ('hand_pose_world', 'gripper_open')}
            request.update(observation_id=obs.key, max_steps=64,
                           target_source='fresh Astra pixel plus legal depth; operator-defined correction; unknown clearance')
            envelope = dict(command_id=uuid4().hex, action=request)
            write_json(args.output/f'{index:02d}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            write_json(args.output/f'{index:02d}_receipt.json', result.receipt.to_dict())
            obs = result.observation
            write_json(args.output/f'{index:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{index:02d}_{role}.png').write_bytes(png_bytes(pixels))
            print(stage['name'], result.receipt.to_dict(), flush=True)
            if result.receipt.reason != 'local stage arrived':
                raise RuntimeError('Nonarrival: stop without retry or subsequent stages')
        write_json(args.output/'result.json', dict(stages=len(stages), actions=64*len(stages),
                   final_observation_id=obs.key, grasp_verified=False,
                   limitation='Endpoint arrival is not grasp or task verification; inspect final images independently'))
    finally:
        client.close()


if __name__ == '__main__':
    main()
