#!/usr/bin/env python3
"""Execute a fresh reviewed elevated carry on the held episode; never reset/retry."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.carry import carry_stages, standoff_stages, reviewed_standoff_stages
from physical_exec.carry import validate_lift_diagnostic, lift_endpoint_completed
from physical_exec.carry import coarse_approach_stage
from physical_exec.imaging import png_bytes
from physical_exec.trace import write_json
from physical_exec.transport import LocalClient, decode_observation, decode_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--standoff-review', type=Path,
                        help='Execute a current reviewed history-based closer-look candidate')
    parser.add_argument('--coarse-approach-review', type=Path,
                        help='Explicit current-depth 4cm approach with >=8cm nominal gap; no insertion')
    parser.add_argument('--exploratory-standoff',action='store_true',
                        help='Current feature measurements; <=10 cm down, >=12 cm nominal standoff, no insertion')
    parser.add_argument('--near-standoff',action='store_true',
                        help='With exploratory-standoff: <=6cm down, >=6cm nominal gap, matched endpoint required')
    parser.add_argument('--contact-hypothesis',action='store_true',
                        help='Explicit simulator contact test to measured plane; <=8cm, no extra push/release')
    parser.add_argument('--contact-tracking-guard', action='store_true',
                        help='Require and attach the per-action tracking guard')
    parser.add_argument('--lift-diagnostic-completion', action='store_true',
                        help='Upward diagnostic only: assess final motion at 10mm / .03rad; not grasp verification')
    args = parser.parse_args()
    if args.coarse_approach_review and (args.standoff_review or args.exploratory_standoff
            or args.near_standoff or args.contact_hypothesis or args.lift_diagnostic_completion
            or not args.contact_tracking_guard):
        parser.error('Coarse approach requires tracking guard and excludes all other modes')
    if args.lift_diagnostic_completion and (not args.contact_tracking_guard
            or args.standoff_review or args.exploratory_standoff
            or args.near_standoff or args.contact_hypothesis):
        parser.error('Lift completion requires guarded upward diagnostic, excludes standoff/contact modes')
    if args.standoff_review and (args.exploratory_standoff or args.near_standoff or args.contact_hypothesis):
        parser.error('Reviewed standoff excludes measurement/contact modes')
    if args.near_standoff and not args.exploratory_standoff:
        parser.error('--near-standoff requires --exploratory-standoff')
    if args.contact_hypothesis and (not args.exploratory_standoff or args.near_standoff):
        parser.error('--contact-hypothesis requires exploratory-standoff and excludes near-standoff')
    plan = json.loads(args.plan.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        meta = client.call('/metadata')
        if args.contact_hypothesis and not meta.get('contact_tracking_guard_enabled'):
            raise ValueError('Contact tests require the per-action tracking guard; current worker is too old')
        if (args.contact_tracking_guard or args.standoff_review) and not meta.get('contact_tracking_guard_enabled'):
            raise ValueError('Worker does not advertise the per-action tracking guard')
        if (meta.get('real_hardware_supported') is not False or not meta.get('local_stages_enabled')
                or not meta.get('continuous_transit_enabled')):
            raise ValueError('Requires simulator continuous local stages')
        obs = decode_observation(client.call('/observe'))
        if args.coarse_approach_review:
            review = json.loads(args.coarse_approach_review.read_text())
            stages = [coarse_approach_stage(plan, review, obs.key, obs.eef_pose,
                                           meta.get('last_gripper_command'))]
            write_json(args.output/'review.json', review)
        elif args.standoff_review:
            review = json.loads(args.standoff_review.read_text())
            stages = reviewed_standoff_stages(plan, review, obs.key, obs.eef_pose,
                                             meta.get('last_gripper_command'), obs.control_dt)
            write_json(args.output/'review.json', review)
        else:
            compiler = standoff_stages if args.exploratory_standoff else carry_stages
            stages = compiler(plan, obs.key, obs.eef_pose, meta.get('last_gripper_command'),
                              **({'near':args.near_standoff,'contact':args.contact_hypothesis}
                                 if args.exploratory_standoff else {}))
        if args.contact_tracking_guard:
            for stage in stages:
                stage['contact_tracking_guard'] = True
        if args.lift_diagnostic_completion:
            validate_lift_diagnostic(stages, obs.eef_pose)
            write_json(args.output/'completion_policy.json', dict(
                scope='upward diagnostic final endpoint only', position_bound_m=.01,
                rotation_bound_rad=.03, grasp_verified=False,
                hard_worker_abort_checks='unchanged', raw_receipts='preserved'))
        write_json(args.output/'source_plan.json', plan)
        write_json(args.output/'declared_sequence.json', stages)
        write_json(args.output/'initial.json', obs.public_state())
        actions = 0
        for i, stage in enumerate(stages):
            action = dict(stage, observation_id=obs.key)
            request = dict(command_id=uuid4().hex, action=action)
            write_json(args.output/f'{i:02d}_request.json', request)
            result = decode_result(client.call('/local-stage', request, mutating=True))
            obs = result.observation
            write_json(args.output/f'{i:02d}_receipt.json', result.receipt.to_dict())
            write_json(args.output/f'{i:02d}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{i:02d}_{role}.png').write_bytes(png_bytes(pixels))
            actions += result.receipt.executed_steps
            print(result.receipt.to_dict(), flush=True)
            expected = 'local stage arrived' if stage['settle_at_end'] else 'transit waypoint passed'
            passed = result.receipt.reason == expected
            if args.lift_diagnostic_completion and i == len(stages)-1:
                passed = lift_endpoint_completed(result.receipt.to_dict())
                write_json(args.output/'completion_assessment.json', dict(
                    motion_within_lift_bounds=passed, grasp_verified=False,
                    strict_arrival=result.receipt.reason == 'local stage arrived'))
            if not passed:
                raise RuntimeError('Carry nonarrival; no retry or subsequent stage')
        write_json(args.output/'result.json', dict(final_observation_id=obs.key, actions=actions,
                   insertion_verified=False, limitation='Endpoint only; fresh visual review required'))
    finally:
        client.close()


if __name__ == '__main__':
    main()
