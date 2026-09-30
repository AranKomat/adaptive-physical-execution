#!/usr/bin/env python3
"""Fresh simulator-only hold then 1 cm upward correction; no model calls or object contact intended."""
import argparse
import os
from pathlib import Path
import sys
from uuid import uuid4
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.transport import LocalClient, decode_observation, decode_result
from physical_exec.trace import write_json
from physical_exec.imaging import png_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--contact-tracking-guard', action='store_true',
                        help='qualify guard-enabled free-space execution; does not test a contact stall')
    parser.add_argument('--ramp-return-qualification', action='store_true',
                        help='Fresh worker only: guarded 12cm upward excursion and return; 256 actions maximum')
    parser.add_argument('--motion-profile', choices=['conservative', 'elevated_open_2x',
                        'elevated_open_5x', 'elevated_open_10x'], default='conservative')
    args = parser.parse_args()
    if args.motion_profile != 'conservative' and not args.ramp_return_qualification:
        raise ValueError('experimental speed requires explicit ramp-return qualification')
    args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient(args.url, os.environ['PHYSICAL_EXEC_SIM_TOKEN'], timeout=180)
    try:
        metadata = client.call('/metadata')
        if not metadata.get('local_stages_enabled') or metadata.get('real_hardware_supported') is not False:
            raise ValueError('requires explicitly enabled simulation worker')
        if args.contact_tracking_guard and not metadata.get('contact_tracking_guard_enabled'):
            raise ValueError('worker does not advertise contact tracking guard')
        if args.ramp_return_qualification and (not args.contact_tracking_guard or
                metadata.get('position_integral_antiwindup') != 'opposing_axis_reset_above_1mm'):
            raise ValueError('ramp return requires guarded anti-windup worker')
        if args.motion_profile != 'conservative' and args.motion_profile not in metadata.get('local_motion_profiles', {}):
            raise ValueError('worker does not advertise requested speed profile')
        write_json(args.output/'metadata.json', metadata)
        obs = decode_observation(client.call('/reset', {'seed': 0}, mutating=True))
        write_json(args.output/'initial.json', obs.public_state())
        phases = [('hold',30,0.), ('upward_1cm',60,.01)]
        origin = obs.eef_pose.copy()
        if args.ramp_return_qualification:
            from physical_exec.geometry import matrix_pose, pose_matrix
            from physical_exec.kinematics import URDFKinematics
            if obs.gripper_open < .999 or obs.seq != 0:
                raise ValueError('requires fresh open-hand state')
            phases = [('up_transit',64,.06), ('up_arrive',64,.12),
                      ('down_transit',64,.06), ('down_arrive',64,0.)]
            if args.motion_profile in ('elevated_open_5x', 'elevated_open_10x'):
                phases = [('up_arrive',64,.12), ('down_arrive',64,0.)]
            kin = URDFKinematics.from_urdf(Path(__file__).resolve().parents[1]/
                'upstream/EmbodiedSWE/robobench/robots/assets/franka/panda_kinematics.urdf')
            base = matrix_pose(pose_matrix(origin) @ np.linalg.inv(pose_matrix(kin.fk(obs.joints))))
            seed = obs.joints.copy()
            for _, _, offset in phases:
                target = origin.copy()
                target[2] += offset
                if not .3 <= target[2] <= .8:
                    raise ValueError('qualification outside elevated workspace')
                result = kin.solve(target, seed, base, iterations=300)
                if not result.converged:
                    raise ValueError('qualification waypoint IK failed; no motion')
                seed = result.joints
        write_json(args.output/'phases.json', phases)
        for index, (name, steps, dz) in enumerate(phases):
            target = obs.eef_pose.copy()
            if args.ramp_return_qualification:
                target = origin.copy()
            target[2] += dz
            request = dict(observation_id=obs.key, hand_pose_world=target.tolist(),
                           gripper_open=1., max_steps=steps, target_source='robot-only '+name+' qualification; unknown clearance')
            if args.ramp_return_qualification:
                request['settle_at_end'] = name.endswith('arrive')
                request['motion_profile'] = args.motion_profile
            if args.contact_tracking_guard:
                request['contact_tracking_guard'] = True
            envelope = dict(command_id=uuid4().hex, action=request)
            write_json(args.output/f'{index}_request.json', envelope)
            result = decode_result(client.call('/local-stage', envelope, mutating=True))
            write_json(args.output/f'{index}_receipt.json', result.receipt.to_dict())
            obs = result.observation
            write_json(args.output/f'{index}_observation.json', obs.public_state())
            for role, pixels in obs.images.items():
                (args.output/f'{index}_{role}.png').write_bytes(png_bytes(pixels))
            print(result.receipt.to_dict(), flush=True)
            expected = ('transit waypoint passed' if request.get('settle_at_end') is False
                        else 'local stage arrived')
            if result.receipt.reason != expected:
                raise RuntimeError('stage did not arrive; stop without subsequent motion')
    finally:
        client.close()


if __name__ == '__main__':
    main()
