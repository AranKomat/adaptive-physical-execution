#!/usr/bin/env python3
"""Bounded sensor-target OSC pilot, using file commands while physics is paused.

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
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args()
    args.enable_cameras = True
    args.output.mkdir(parents=True, exist_ok=False)
    app = AppLauncher(args).app
    import numpy as np
    import torch
    from physical_exec.geometry import pose_error
    from physical_exec.imaging import png_bytes
    from physical_exec.osc_reference import ReferenceOSC, validate_plan
    from physical_exec.trace import write_json
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
    sim = module.load_sim('assembly.pc_gpu.franka.osc', control_space=None,
                          size=tuple(task['image_size']), cams=tuple(task['camera_map'].values()), warmup=0)
    replay._camera_cfg = old_camera_cfg
    scene_cls.CAMERAS = old_cameras
    env = sim.env
    env.reset(seed=0)
    art = env.robot.articulation
    hand = art.body_names.index('panda_hand')
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
    controller = ReferenceOSC()
    result = dict(condition='sensor-target OSC pilot; exploratory unknown clearance; grasp assistance enabled',
                  model_controls_targets=True, stages=[], success_claimed=False)
    write_json(args.output / 'metadata.json', dict(episode=episode, control_dt=env.dt*env.robot.control_period,
        controller='ported frozen Motion OSC gains', action_budget=700, frame_kind='sampled every 10 actions',
        camera_map=task['camera_map'], initial_warmup_actions=0, privileged_control_inputs=False))
    started = time.monotonic()
    try:
        state = capture()
        for index in range(4):
            write_json(args.output / 'ready.json', dict(command_index=index, **state))
            print('READY', index, state['observation_id'], flush=True)
            path = args.output / f'command_{index}.json'
            deadline = time.monotonic() + 1800
            while not path.exists():
                if time.monotonic() > deadline:
                    raise TimeoutError('No command within 30 minutes; no motion retry')
                time.sleep(1)
            command = json.loads(path.read_text())
            phases = validate_plan(command, state['observation_id'], 700-seq)
            with (args.output / 'robot_actions.jsonl').open('a') as log:
                for phase in phases:
                    target = np.asarray(phase['hand_pose_world'])
                    for _ in range(phase['actions']):
                        state = robot_state()
                        if not np.isfinite(state['joints'] + state['joint_velocities']).all():
                            raise RuntimeError('nonfinite robot telemetry')
                        action = controller.command(state['hand_pose_world'], target, phase['finger_position_m'])
                        env.step(torch.as_tensor(action[None], dtype=torch.float32, device=env.device))
                        seq += 1
                        state = robot_state()
                        log.write(json.dumps(dict(phase=phase['name'], action=action.tolist(), **state))+'\n')
                        log.flush()
                        if seq % 10 == 0:
                            capture(depth=False)
                    state = capture()
                    error = pose_error(state['hand_pose_world'], target)
                    row = dict(name=phase['name'], observation_id=state['observation_id'],
                               position_error_m=float(np.linalg.norm(error[:3])),
                               rotation_error_rad=float(np.linalg.norm(error[3:])))
                    result['stages'].append(row)
                    print('PHASE', json.dumps(row), flush=True)
                    if row['position_error_m'] > .02 or row['rotation_error_rad'] > .15:
                        raise RuntimeError('phase arrival failed; no automatic continuation')
            if command['finish']:
                break
    except Exception:
        result['error'] = traceback.format_exc()
        traceback.print_exc()
    finally:
        result.update(actions=seq, wall_seconds=time.monotonic()-started)
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
