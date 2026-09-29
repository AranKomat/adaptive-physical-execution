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
from probe_contact_stage import exploratory_completion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pause-before-close', action='store_true',
                        help='Stop after descent for a separate fresh visual contact-geometry review')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--pause-at-standoff', action='store_true')
    mode.add_argument('--grasp-only', action='store_true', help='Resume from a fresh close-range target')
    parser.add_argument('--lift-height', type=float, default=.05)
    parser.add_argument('--phase-completion', action='store_true',
                        help='Use predeclared exploratory bounds for closure/lift only')
    parser.add_argument('--continuous-transit', action=argparse.BooleanOptionalAction, default=True,
                        help='Pass intermediate same-phase waypoints without fixed settling holds (default); '
                             '--no-continuous-transit reproduces legacy fixed holds')
    parser.add_argument('--contact-tracking-guard', action='store_true',
                        help='Require and attach the simulator contact tracking guard to stages')
    args = parser.parse_args()
    if not math.isfinite(args.lift_height) or not 0 < args.lift_height <= .23:
        raise ValueError('Lift height must be in (0, 0.23] m')
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
        if args.continuous_transit and not metadata.get('continuous_transit_enabled'):
            raise ValueError('Worker must be restarted with continuous-transit implementation')
        if args.contact_tracking_guard and not metadata.get('contact_tracking_guard_enabled'):
            raise ValueError('Worker must advertise the contact tracking guard')
        obs = decode_observation(client.call('/observe'))
        if obs.key != plan['observation_id']:
            raise ValueError('Target plan is not current; no automatic reset or retry')
        if args.grasp_only and obs.gripper_open < .95:
            raise ValueError('Grasp-only continuation requires an already open gripper')
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
                     ('short_lift', np.r_[hand+[0,0,args.lift_height], top], .3)]
        if args.grasp_only:
            endpoints = endpoints[3:]
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
        if args.continuous_transit:
            for index, stage in enumerate(stages):
                stage['settle_at_end'] = (index == len(stages)-1
                    or stages[index+1]['name'] != stage['name'] or stage['name'] == 'close')
        write_json(args.output/'declared_sequence.json', stages)
        write_json(args.output/'completion_policy.json', dict(
            exploratory_contact_completion=args.phase_completion,
            lift_height_m=args.lift_height, position_bound_m=.01, rotation_bound_rad=.15,
            hard_worker_abort_checks='unchanged', grasp_verified=False))
        executed_actions = 0
        for index, stage in enumerate(stages):
            if stage['name'] == 'descend' and args.pause_at_standoff:
                write_json(args.output/'result.json', dict(stages=index, actions=executed_actions,
                           final_observation_id=obs.key, grasp_verified=False,
                           terminal_reason='awaiting_close_range_target'))
                print('Paused at standoff at '+obs.key, flush=True)
                return
            if stage['name'] == 'close' and args.pause_before_close:
                write_json(args.output/'result.json', dict(stages=index, actions=executed_actions,
                           final_observation_id=obs.key, grasp_verified=False,
                           terminal_reason='awaiting_preclosure_review',
                           limitation='No closure or lift authorized by target selection alone'))
                print('Paused before closure at '+obs.key, flush=True)
                return
            request = {key: stage[key] for key in ('hand_pose_world', 'gripper_open')}
            if args.continuous_transit:
                request['settle_at_end'] = stage['settle_at_end']
            request.update(observation_id=obs.key, max_steps=64,
                           target_source=plan.get('target_source', 'unspecified target source')
                           + '; operator-defined correction; unknown clearance')
            if args.contact_tracking_guard:
                request['contact_tracking_guard'] = True
            envelope = dict(command_id=uuid4().hex, action=request)
            write_json(args.output/f'{index:02d}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            executed_actions += result.receipt.to_dict()['executed_steps']
            write_json(args.output/f'{index:02d}_receipt.json', result.receipt.to_dict())
            obs = result.observation
            write_json(args.output/f'{index:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{index:02d}_{role}.png').write_bytes(png_bytes(pixels))
            print(stage['name'], result.receipt.to_dict(), flush=True)
            contact_phase = stage['name'] in ('close', 'short_lift') and args.phase_completion
            passed = (result.receipt.reason == 'transit waypoint passed'
                      if stage.get('settle_at_end') is False else
                      exploratory_completion(result.receipt.to_dict()) if contact_phase
                      else result.receipt.reason == 'local stage arrived')
            if not passed:
                raise RuntimeError('Nonarrival: stop without retry or subsequent stages')
        write_json(args.output/'result.json', dict(stages=len(stages), actions=executed_actions,
                   final_observation_id=obs.key, grasp_verified=False,
                   limitation='Endpoint arrival is not grasp or task verification; inspect final images independently'))
    finally:
        client.close()


if __name__ == '__main__':
    main()
