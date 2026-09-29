#!/usr/bin/env python3
"""Bounded sensor-target OSC/native-DiffIK pilot, with paused-world file commands.

Not the standard IK/FLUX service and not a collision-certified controller.
Only final evaluator output reads scene object state; planning captures exclude it.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--task', type=Path, default=Path('configs/tasks/pc_gpu.json'))
    p.add_argument('--ramp-targets', action='store_true', help='0.0225 m/s translation ramp at actual controller cadence')
    p.add_argument('--controller', choices=['osc','diff_ik'], default='osc')
    p.add_argument('--max-reference-actions', type=int, default=700, help='episode cap in 15 Hz action equivalents, at most 2000')
    p.add_argument('--integral-feedback', action='store_true',help='native DiffIK bounded translation integral and 3 cm command cap')
    p.add_argument('--pause-on-arrival-failure', action='store_true',help='nonterminal timeout only; unsafe motion stops stay terminal')
    p.add_argument('--inspection-camera', action='store_true', help='opt-in idealized right-camera positioning; no collision body')
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args()
    if not 1 <= args.max_reference_actions <= 2000:
        raise ValueError('invalid bounded episode budget')
    if args.integral_feedback and args.controller != 'diff_ik':
        raise ValueError('integral-feedback flag is for native DiffIK only')
    args.enable_cameras = True
    args.output.mkdir(parents=True, exist_ok=False)
    app = AppLauncher(args).app
    import numpy as np
    import torch
    from physical_exec.geometry import pose_error
    from physical_exec.imaging import png_bytes
    from physical_exec.osc_reference import (ReferenceOSC, NativeDiffIKFeedback, validate_plan,
                                            phases_at_cadence, ramped_target, motion_stop_reason)
    from physical_exec.trace import write_json
    from physical_exec.inspection_camera import camera_path
    repo = args.repo.resolve()
    for path in (repo, repo / 'vla/eval', repo / 'data_engine', repo / 'vla/convert'):
        sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location('_sensor_osc_sim', repo / 'vla/eval/sim.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    import robobench
    robobench.discover()
    from robobench.core import SCENES
    from engine import replay
    task = json.loads(args.task.read_text())
    scene_cls = SCENES.get('pc_gpu')
    old_cameras = getattr(scene_cls, 'CAMERAS', {})
    scene_cls.CAMERAS = {**old_cameras, **task['extra_cameras']}
    old_camera_cfg = replay._camera_cfg
    def camera_cfg(*a, **kw):
        cfg = old_camera_cfg(*a, **kw)
        cfg.data_types = ['rgb', 'distance_to_image_plane']
        cfg.update_latest_camera_pose = True
        return cfg
    replay._camera_cfg = camera_cfg
    sim = module.load_sim('assembly.pc_gpu.franka.'+args.controller, control_space=None,
                          size=tuple(task['image_size']), cams=tuple(task['camera_map'].values()), warmup=0)
    replay._camera_cfg = old_camera_cfg
    scene_cls.CAMERAS = old_cameras
    env = sim.env
    env.reset(seed=0)
    art = env.robot.articulation
    hand = art.body_names.index('panda_hand')
    arm_limits = art.data.joint_pos_limits[0, sim.arm_ids].detach().cpu().numpy()
    episode = uuid4().hex
    seq = 0
    def array(value):
        return value.detach().cpu().numpy()
    def robot_state():
        return dict(observation_id=f'{episode}:{seq}',
                    hand_pose_world=np.r_[array(art.data.body_pos_w)[0, hand],
                                          array(art.data.body_quat_w)[0, hand]].tolist(),
                    joint_names=list(art.joint_names), joints=array(art.data.joint_pos)[0].tolist(),
                    joint_velocities=array(art.data.joint_vel)[0].tolist())
    def capture(depth=True):
        directory = args.output / 'captures' / f'{seq:06d}'
        directory.mkdir(parents=True, exist_ok=True)
        for _ in range(4):
            env.sim.render()
        state = robot_state()
        write_json(directory / 'state.json', state)
        for role, name in task['camera_map'].items():
            sensor = sim.sensors[name]
            sensor.update(0., force_recompute=True)
            data = sensor.data
            (directory / f'{role}.png').write_bytes(png_bytes(array(data.output['rgb'])[0, ..., :3]))
            if depth:
                np.save(directory / f'{role}_depth.npy', array(data.output['distance_to_image_plane'])[0, ..., 0])
                write_json(directory / f'{role}_calibration.json', dict(
                    observation_id=state['observation_id'], depth_convention='camera_optical_z', depth_units='meters',
                    intrinsic_matrix=array(data.intrinsic_matrices)[0].tolist(),
                    camera_position_world=array(data.pos_w)[0].tolist(),
                    camera_quaternion_world_wxyz_optical=array(data.quat_w_ros)[0].tolist(),
                    source='idealized legal RGB-D sensor; no object state'))
        return state
    control_dt = env.dt*env.robot.control_period
    budget = round(args.max_reference_actions/(15*control_dt))
    record_every = max(1,round((2/3)/control_dt))
    native_cfg = env.robot.controller.controllers[0].cfg
    controller = (ReferenceOSC() if args.controller == 'osc' else
                  NativeDiffIKFeedback(native_cfg.pos_scale,native_cfg.rot_scale,
                                       control_dt=control_dt,integral_feedback=args.integral_feedback))
    result = dict(condition=f'sensor-target {args.controller} pilot; exploratory unknown clearance; grasp assistance enabled',
                  target_provenance='file commands; inspect target_source in each command',
                  stages=[], success_claimed=False)
    write_json(args.output / 'metadata.json', dict(episode=episode, control_dt=control_dt,
        controller=('ported frozen Motion OSC gains' if args.controller=='osc' else 'native DiffIK with bounded absolute-target feedback'),
        native_declared_control_dt=native_cfg.dt, physics_dt=env.dt,
        integral_feedback=args.integral_feedback, pause_on_arrival_failure=args.pause_on_arrival_failure,
        native_translation_command_cap_m=(.03 if args.integral_feedback else .01) if args.controller=='diff_ik' else None,
        action_budget=budget, reference_action_budget_15hz=args.max_reference_actions,
        frame_kind=f'sampled every {record_every} actions',
        extra_cameras=task['extra_cameras'], image_size=task['image_size'],
        inspection_camera=args.inspection_camera,
        camera_collision_model='none; idealized sensor-position experiment, clearance unknown',
        camera_map=task['camera_map'], initial_warmup_actions=0, privileged_control_inputs=False,
        ramp_targets=args.ramp_targets, rotation_abort_rad=.35, joint_limit_margin_rad=.005))
    started = time.monotonic()
    command_wait_seconds = 0.
    try:
        state = capture()
        for index in range(8):
            write_json(args.output / 'ready.json', dict(command_index=index,
                       last_stage=result['stages'][-1] if result['stages'] else None, **state))
            print('READY', index, state['observation_id'], flush=True)
            path = args.output / f'command_{index}.json'
            wait_started = time.monotonic()
            deadline = wait_started + 1800
            while not path.exists():
                if time.monotonic() > deadline:
                    raise TimeoutError('No command within 30 minutes; no motion retry')
                time.sleep(1)
            command_wait_seconds += time.monotonic() - wait_started
            command = json.loads(path.read_text())
            scaled_command = {**command,'phases':phases_at_cadence(command,control_dt)}
            phases = validate_plan(scaled_command, state['observation_id'], budget-seq,
                                   max_phase_actions=round(12/control_dt))
            with (args.output / 'robot_actions.jsonl').open('a') as log:
                for phase in phases:
                    phase_started = time.monotonic()
                    target = np.asarray(phase['hand_pose_world'])
                    phase_start = robot_state()['hand_pose_world']
                    eye_path = None
                    if 'camera_eye_world' in phase:
                        if not args.inspection_camera:
                            raise ValueError('inspection camera requires explicit opt-in')
                        moving_camera = sim.sensors[task['camera_map']['right']]
                        # Pinned IsaacLab Fabric camera writes did not persist in
                        # the live test. Use its USD pose path for this sensor only,
                        # so rendering and calibration query the same transform.
                        if not hasattr(moving_camera._view, '_use_fabric'):
                            raise RuntimeError('unsupported inspection camera transform backend')
                        moving_camera._view._use_fabric = False
                        moving_camera.update(0., force_recompute=True)
                        eye_path = camera_path(array(moving_camera.data.pos_w)[0], phase['camera_eye_world'],
                                               phase_start, target, phase['actions'], control_dt)
                    for tick in range(phase['actions']):
                        state = robot_state()
                        if not np.isfinite(state['joints'] + state['joint_velocities']).all():
                            raise RuntimeError('nonfinite robot telemetry')
                        stop = motion_stop_reason(state['hand_pose_world'],target,np.asarray(state['joints'])[sim.arm_ids],arm_limits)
                        if stop:
                            raise RuntimeError(stop)
                        waypoint = ramped_target(phase_start,target,tick+1, .0225*control_dt) if args.ramp_targets else target
                        action = controller.command(state['hand_pose_world'], waypoint, phase['finger_position_m'])
                        if eye_path is not None:
                            moving_camera.set_world_poses_from_view(
                                torch.as_tensor(eye_path[tick][None], dtype=torch.float32, device=env.device),
                                torch.as_tensor([task['extra_cameras'][task['camera_map']['right']]['target']],
                                                dtype=torch.float32, device=env.device))
                        env.step(torch.as_tensor(action[None], dtype=torch.float32, device=env.device))
                        seq += 1
                        state = robot_state()
                        log.write(json.dumps(dict(phase=phase['name'], action=action.tolist(),
                            camera_eye_command=None if eye_path is None else eye_path[tick].tolist(), **state))+'\n')
                        log.flush()
                        stop = motion_stop_reason(state['hand_pose_world'],target,np.asarray(state['joints'])[sim.arm_ids],arm_limits)
                        if stop:
                            raise RuntimeError(stop)
                        if seq % record_every == 0:
                            capture(depth=False)
                    state = capture()
                    error = pose_error(state['hand_pose_world'], target)
                    row = dict(name=phase['name'], observation_id=state['observation_id'],
                               execution_wall_seconds=time.monotonic()-phase_started,
                               simulated_seconds=phase['actions']*control_dt,
                               position_error_m=float(np.linalg.norm(error[:3])),
                               rotation_error_rad=float(np.linalg.norm(error[3:])))
                    row['arrival_passed'] = row['position_error_m'] <= .02 and row['rotation_error_rad'] <= .15
                    if eye_path is not None:
                        actual_eye = array(moving_camera.data.pos_w)[0]
                        row['camera_position_error_m'] = float(np.linalg.norm(actual_eye-eye_path[-1]))
                        row['arrival_passed'] = row['arrival_passed'] and row['camera_position_error_m'] <= .001
                    result['stages'].append(row)
                    print('PHASE', json.dumps(row), flush=True)
                    if not row['arrival_passed']:
                        if args.pause_on_arrival_failure and not command['finish']:
                            print('ARRIVAL_TIMEOUT_PAUSED; remaining phases skipped',flush=True)
                            break
                        raise RuntimeError('phase arrival failed; no automatic continuation')
            if command['finish']:
                break
    except Exception:
        result['error'] = traceback.format_exc()
        traceback.print_exc()
    finally:
        capture()
        result.update(actions=seq, simulated_seconds=seq*control_dt, wall_seconds=time.monotonic()-started,
                      completed_command_wait_seconds=command_wait_seconds)
        write_json(args.output / 'result.json', result)
        # Scoring only AFTER all control; never read by the command-generating path.
        write_json(args.output / 'evaluator_only.json', dict(
            scene_success=bool(env.scene.success().all()), grasp_held=bool(env.scene.grasp_held.any()),
            card_position=array(env.scene.card.data.root_pos_w)[0].tolist(),
            card_velocity=array(env.scene.card.data.root_lin_vel_w)[0].tolist(),
            warning='privileged final scoring, not policy input'))
        print('FINISHED', json.dumps(result), flush=True)
    os._exit(2 if 'error' in result else 0)


if __name__ == '__main__':
    main()
