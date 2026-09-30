"""Source-backed EvalSim integration for ONE Franka PC assembly environment.

Needs upstream commit d34837e..., Isaac Sim/Lab and assets. Not GPU-validated
in the build environment. All simulator/torch imports are lazy. AppLauncher
MUST already exist; use scripts/serve_embodiedswe.py rather than importing Isaac
from the policy process. No task-code access is exposed to the model.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import time
from uuid import uuid4
import numpy as np
from ..contracts import Observation, ActionChunk, StepResult, ExecutionReceipt, Evaluation
from ..errors import InputRejected, AmbiguousExecution
from ..geometry import pose_error
from ..kinematics import URDFKinematics
from ..safety import Limits, validate_chunk
from ..imaging import png_bytes
from ..trace import write_json, sha256_file


class EmbodiedSWEEnvironment:
    def __init__(self, repo: str | Path, task: dict, limits: Limits, device="cuda:0", record_dir=None,
                 record_depth=False, allow_local_stages=False, local_stage_rotation_integral=False,
                 allow_inspection_camera=False):
        self.allow_local_stages = allow_local_stages
        self.local_stage_rotation_integral = local_stage_rotation_integral
        self.allow_inspection_camera = allow_inspection_camera
        self._last_gripper_command = None
        self._transit_context = None
        if allow_inspection_camera and not (allow_local_stages and record_depth):
            raise ValueError('inspection camera requires local stages and recorded depth/calibration')
        if record_depth and record_dir is None:
            raise ValueError("depth capture requires a recording directory")
        self.record_depth = record_depth
        repo = Path(repo).resolve()
        path = repo / "vla/eval/sim.py"
        if not path.is_file(): raise FileNotFoundError(f"clone the pinned EmbodiedSWE checkout first: {path}")
        for p in (repo, repo/"vla/eval", repo/"data_engine", repo/"vla/convert"):
            sys.path.insert(0, str(p))
        spec = importlib.util.spec_from_file_location("_physical_exec_evalsim", path)
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
        import robobench
        robobench.discover()
        from robobench.core.registries import ENVS, SCENES
        preset = task["preset"]
        if preset not in ENVS.list(): raise ValueError(f"unknown upstream env {preset}; run the upstream --list command")
        cfg = ENVS.get(preset)()
        if cfg.robot != "franka": raise ValueError("first adapter release supports Franka only")
        scene_cls = SCENES.get(cfg.scene)
        original_cameras = getattr(scene_cls, "CAMERAS", None)
        # Static operator-specified camera installation, not task-object-ground-truth queries.
        extra = task.get("extra_cameras", {})
        if extra: scene_cls.CAMERAS = {**(original_cameras or {}), **extra}
        from engine import replay
        original_camera_cfg = replay._camera_cfg
        def camera_cfg_with_depth(name, view, size, surface_z):
            from ..config import configured_camera_view
            cfg = original_camera_cfg(name, configured_camera_view(task, name, view), size, surface_z)
            if record_depth:
                cfg.data_types = [*cfg.data_types, "distance_to_image_plane"]
            # Link-mounted cameras move after initialization; cached spawn poses
            # cannot calibrate their current rendered depth.
            cfg.update_latest_camera_pose = True
            return cfg
        if record_depth or 'wrist_target_hand' in task:
            replay._camera_cfg = camera_cfg_with_depth
        try:
            self.sim = module.load_sim(preset, num_envs=1, device=device,
                                       control_space="joint_pos", control_freq_hz=float(task.get("control_hz", 15)),
                                       size=tuple(task.get("image_size", [640, 360])),
                                       cams=tuple(task["camera_map"].values()), warmup=12)
        finally:
            replay._camera_cfg = original_camera_cfg
            if extra:
                if original_cameras is None: delattr(scene_cls, "CAMERAS")
                else: scene_cls.CAMERAS = original_cameras
        self.repo, self.task_config, self.limits = repo, task, limits
        self.camera_map = task["camera_map"]
        if len(set(self.camera_map.values())) != len(self.camera_map):
            raise ValueError("camera duplication is not a substitute for missing views")
        for source in self.camera_map.values():
            if source not in self.sim.sensors: raise ValueError(f"camera {source} not available")
        self.kin = URDFKinematics.from_urdf(self.sim.env.robot.cfg.franka_urdf)
        self.joint_names = tuple(self.sim.arm_names)
        if self.joint_names != self.kin.joint_names:
            raise ValueError(f"URDF/simulator joint order mismatch: {self.kin.joint_names} vs {self.joint_names}")
        self.body_index = self.sim.env.robot.articulation.body_names.index("panda_hand")
        self.seq = 0; self.episode_id = None; self.current = None; self.raw = None
        self.record_root = Path(record_dir).resolve() if record_dir else None
        self.record_episode = None
        self._evaluation = Evaluation(native=True)
        self._poisoned = False

    @staticmethod
    def _numpy(v):
        return v.detach().cpu().numpy() if hasattr(v, "detach") else np.asarray(v)

    def _base(self):
        d = self.sim.env.robot.articulation.data
        return np.r_[self._numpy(d.root_pos_w)[0], self._numpy(d.root_quat_w)[0]]

    def _measured_eef(self):
        d = self.sim.env.robot.articulation.data
        return np.r_[self._numpy(d.body_pos_w)[0, self.body_index], self._numpy(d.body_quat_w)[0, self.body_index]]

    def _extract(self, raw) -> Observation:
        state = np.asarray(raw["state"])[0]
        if state.shape != (8,): raise ValueError("expected seven Franka joints plus closedness")
        imgs = {role: np.asarray(raw["images"][name])[0, ..., :3] for role, name in self.camera_map.items()}
        obs = Observation(self.episode_id, self.seq, self.seq/self.sim.rate_hz,
                          self.task_config["instruction"], "franka", imgs, state[:7], self.joint_names,
                          self._measured_eef(), 1.-float(state[-1]), 1./self.sim.rate_hz)
        # Privileged evaluator values remain host-side, not in Observation.
        self._evaluation = Evaluation(bool(np.asarray(raw["success"])[0]),
                                      float(np.asarray(raw["progress"])[0]), True, "upstream native grader")
        if self.record_episode is not None:
            for role, image in obs.images.items():
                directory = self.record_episode / role; directory.mkdir(exist_ok=True)
                (directory / f"{self.seq:06d}.png").write_bytes(png_bytes(image))
            if self.record_depth:
                self._record_depth(obs)
        return obs

    def _record_depth(self, obs):
        """Sensor-only recording; excludes object poses, labels and evaluator state."""
        for role, name in self.camera_map.items():
            data = self.sim.sensors[name].data
            depth = self._numpy(data.output["distance_to_image_plane"])[0].squeeze(-1)
            if depth.shape != obs.images[role].shape[:2]:
                raise ValueError("depth/RGB alignment shape mismatch")
            directory = self.record_episode / (role + "_depth")
            directory.mkdir(exist_ok=True)
            np.save(directory / f"{self.seq:06d}.npy", depth, allow_pickle=False)
            write_json(directory / f"{self.seq:06d}.json", {
                "observation_id": obs.key, "depth_units": "meters",
                "depth_convention": "camera_optical_z",
                "source": "idealized simulator depth sensor; not object-state query",
                "intrinsic_matrix": self._numpy(data.intrinsic_matrices)[0].tolist(),
                "camera_position_world": self._numpy(data.pos_w)[0].tolist(),
                "camera_quaternion_world_wxyz_optical": self._numpy(data.quat_w_ros)[0].tolist(),
                "invalid_depth": "nonfinite or nonpositive; preserved in npy",
                "policy_input": False,
            })

    def reset(self, seed):
        if self.episode_id is not None: raise InputRejected("one episode per worker, no in-episode reset")
        self.episode_id = uuid4().hex; self.seq = 0
        if self.record_root is not None:
            self.record_episode = self.record_root / self.episode_id
            self.record_episode.mkdir(parents=True, exist_ok=False)
            write_json(self.record_episode/"recording.json", {"fps": self.sim.rate_hz, "backend": "embodiedswe",
                       "view_roles": list(self.camera_map), "time_model": "physics_paused_during_inference",
                       "frame_kind": "every_control_latch", "metadata": self.metadata()})
        self.raw = self.sim.reset(seed=seed)
        self.current = self._extract(self.raw)
        self.base_pose = self._base()
        error = pose_error(self.kin.fk(self.current.joints, self.base_pose), self.current.eef_pose)
        if np.linalg.norm(error[:3]) > .005 or np.linalg.norm(error[3:]) > .05:
            raise ValueError(f"robot-only FK qualification failed: {error.tolist()}; check URDF/root/hand frame")
        return self.current

    def step(self, action: ActionChunk, command_id: str) -> StepResult:
        if self.current is None: raise InputRejected("reset first")
        if self._poisoned: raise AmbiguousExecution("worker is halted")
        self._transit_context = None
        before = self.current; started = time.monotonic()
        command = validate_chunk(action, before, self.limits, self.kin.limits)
        targets = []
        q = before.joints.copy()
        # Complete validation/IK conversion BEFORE executing anything.
        for row in command.values:
            if command.kind == "joint_absolute":
                q_next = row[:-1]
            else:
                ik = self.kin.solve(row[:7], q, self.base_pose)
                if not ik.converged:
                    raise InputRejected(f"IK not converged: position={ik.position_error_m:.5f}m rotation={ik.rotation_error_rad:.4f}rad")
                q_next = ik.joints
            if np.max(np.abs(q_next-q)) > self.limits.max_joint_step_rad + 1e-8:
                raise InputRejected("IK/joint continuity guard rejected a large joint transition")
            targets.append(np.r_[q_next, 1.-row[-1]])  # EvalSim expects CLOSED fraction
            q = q_next
        count = 0
        try:
            for row in targets:
                self.raw = self.sim.step(np.asarray(row, dtype=np.float32)[None])
                self.seq += 1; count += 1
                self.current = self._extract(self.raw)
                self._last_gripper_command = float(1.-row[-1])
                if self._evaluation.success: break  # host terminates; scorer never sent to model
        except Exception as e:
            self._poisoned = True
            raise AmbiguousExecution(f"simulator error after {count} confirmed latches; do not replay the command") from e
        expected = self.kin.fk(targets[count-1][:-1], self.base_pose)
        error = pose_error(self.current.eef_pose, expected)
        receipt = ExecutionReceipt(command_id, before.key, self.current.key, len(targets), count,
                                   "executed" if count == len(targets) else "interrupted",
                                   "control chunk executed" if count == len(targets) else "host ended the episode during chunk",
                                   action.source, count/self.sim.rate_hz, time.monotonic()-started,
                                   float(np.linalg.norm(error[:3])), float(np.linalg.norm(error[3:])))
        if self.record_episode is not None:
            with (self.record_episode/"native_commands.jsonl").open("a") as f:
                f.write(__import__("json").dumps({"command_id": command_id, "start_seq": before.seq,
                        "joint_targets_and_closedness": np.asarray(targets[:count]).tolist()})+"\n")
        return StepResult(self.current, receipt, self._evaluation)

    def local_stage(self, value, command_id):
        """Explicit feedback correction on the current episode, never an automatic takeover."""
        if not self.allow_local_stages:
            raise InputRejected('local stages not enabled')
        if self.current is None or self._poisoned:
            raise InputRejected('local stage requires an initialized, unpoisoned worker')
        from ..local_stage import validate_local_stage
        from ..osc_reference import NativeDiffIKFeedback, ramped_pose_target, motion_stop_reason
        target = validate_local_stage(value, self.current,
            allow_inspection_camera=self.allow_inspection_camera,
            last_gripper_command=self._last_gripper_command)
        import torch
        eye_path = None
        if 'camera_eye_world' in value:
            from ..inspection_camera import camera_path, camera_gaze_path
            from ..geometry import finite_vector
            moving_camera = self.sim.sensors[self.camera_map['right']]
            if not hasattr(moving_camera._view, '_use_fabric'):
                raise InputRejected('unsupported inspection camera transform backend')
            try:
                gaze = finite_vector(getattr(self, '_inspection_gaze',
                    self.task_config['extra_cameras'][self.camera_map['right']]['target']), 3)
                eye_path = camera_path(self._numpy(moving_camera.data.pos_w)[0], value['camera_eye_world'],
                    self.current.eef_pose, target, value['max_steps'], self.current.control_dt,
                    oblique_envelope=True)
                gaze_path = camera_gaze_path(self._numpy(moving_camera.data.pos_w)[0],
                    eye_path, gaze, value.get('camera_gaze_world', gaze), self.current.control_dt)
            except (ValueError, TypeError, KeyError) as exc:
                raise InputRejected('invalid inspection camera path') from exc
        from robobench.controllers.diff_ik import DiffIKController, DiffIKControllerCfg
        cfg = DiffIKControllerCfg(ee_body='panda_hand', arm_joint_names=self.joint_names)
        solver = DiffIKController(cfg)
        solver.bind(self.sim.env.robot)
        feedback = NativeDiffIKFeedback(cfg.pos_scale, cfg.rot_scale,
                                       control_dt=self.current.control_dt, integral_feedback=True,
                                       rotation_integral_feedback=self.local_stage_rotation_integral)
        before = self.current
        smooth_path = None
        if value.get('motion_profile') in ('elevated_open_5x', 'elevated_open_10x'):
            from ..transit_trajectory import transit_trajectory
            smooth_path = transit_trajectory(before.eef_pose, target,
                speed_scale=5 if value['motion_profile'] == 'elevated_open_5x' else 10,
                dt=before.control_dt)['poses']
        stable_steps = 0
        ramp_start = before.eef_pose
        context = getattr(self, '_transit_context', None)
        self._transit_context = None
        if (context is not None and context['observation_id'] == before.key
                and context['opening'] == value['gripper_open'] and eye_path is None and smooth_path is None):
            ramp_start, feedback, solver = context['target'], context['feedback'], context['solver']
        pass_through = value.get('settle_at_end') is False
        open_arrival = (eye_path is None and not pass_through
                        and value['gripper_open'] == 1.)
        waypoint_passed = False
        contact_stopped = False
        started = time.monotonic()
        completed = 0
        try:
            if eye_path is not None:
                moving_camera._view._use_fabric = False
            for index in range(value['max_steps']):
                state = self.current
                reason = motion_stop_reason(state.eef_pose, target, state.joints, self.kin.limits)
                if reason:
                    raise RuntimeError(reason)
                waypoint = (smooth_path[min(index+1,len(smooth_path)-1)] if smooth_path is not None else
                            ramped_pose_target(ramp_start, target, index+1,
                                              (.045 if value.get('motion_profile') == 'elevated_open_2x' else .0225)*state.control_dt,
                                              (.12 if value.get('motion_profile') == 'elevated_open_2x' else .06)*state.control_dt))
                feedback_args = {}
                if value.get('trajectory_feedforward'):
                    following = smooth_path[min(index+2,len(smooth_path)-1)]
                    feedback_args['trajectory_increment'] = pose_error(waypoint, following)
                raw = feedback.command(state.eef_pose, waypoint, .04*value['gripper_open'], **feedback_args)
                q = self._numpy(solver.compute(torch.as_tensor(raw[:6][None], dtype=torch.float32,
                                                               device=self.sim.env.device)))[0]
                action = ActionChunk('joint_absolute', [np.r_[q, value['gripper_open']]],
                                     state.key, state.control_dt, 'sensor_local_diffik', self.joint_names)
                if eye_path is not None:
                    moving_camera.set_world_poses_from_view(
                        torch.as_tensor(eye_path[index][None], dtype=torch.float32, device=self.sim.env.device),
                        torch.as_tensor(gaze_path[index][None], dtype=torch.float32, device=self.sim.env.device))
                self.step(action, f'{command_id}:{index}')
                completed += 1
                if value.get('contact_tracking_guard'):
                    reason = motion_stop_reason(self.current.eef_pose, target, self.current.joints, self.kin.limits)
                    if reason:
                        raise RuntimeError(reason)
                    contact_error = pose_error(self.current.eef_pose, waypoint)
                    if np.linalg.norm(contact_error[:3]) > .01 or np.linalg.norm(contact_error[3:]) > .10:
                        contact_stopped = True
                        break
                if eye_path is not None:
                    hold_error = pose_error(self.current.eef_pose, target)
                    if np.linalg.norm(hold_error[:3]) > .01 or np.linalg.norm(hold_error[3:]) > .15:
                        raise RuntimeError('inspection arm hold drift exceeded bounds')
                reason = motion_stop_reason(self.current.eef_pose, target, self.current.joints, self.kin.limits)
                if reason:
                    raise RuntimeError(reason)
                ramp_finished = np.linalg.norm(pose_error(waypoint, target)) < 1e-9
                if (eye_path is None and not pass_through and ramp_finished
                        and (smooth_path is not None or open_arrival)):
                    endpoint_error = pose_error(self.current.eef_pose, target)
                    motion = pose_error(state.eef_pose, self.current.eef_pose)
                    stable = (np.linalg.norm(endpoint_error[:3]) <= .003
                              and np.linalg.norm(endpoint_error[3:]) <= .03
                              and np.linalg.norm(motion[:3]) <= .0005
                              and np.linalg.norm(motion[3:]) <= .002
                              and self.current.gripper_open >= .99
                              and abs(self.current.gripper_open-state.gripper_open) <= .001)
                    stable_steps = stable_steps+1 if stable else 0
                    if stable_steps >= 4:
                        break
                if pass_through and np.linalg.norm(pose_error(waypoint, target)) < 1e-9:
                    transit_error = pose_error(self.current.eef_pose, target)
                    if np.linalg.norm(transit_error[:3]) > .01 or np.linalg.norm(transit_error[3:]) > .15:
                        raise RuntimeError('transit tracking error exceeded bounds')
                    waypoint_passed = True
                    break
                if self._evaluation.success:
                    break
            error = pose_error(self.current.eef_pose, target)
            if eye_path is not None:
                camera_error = np.linalg.norm(self._numpy(moving_camera.data.pos_w)[0]-eye_path[-1])
                if completed != value['max_steps'] or camera_error > .001 or not np.isfinite(camera_error):
                    raise RuntimeError('inspection camera did not arrive; no retry')
                if 'camera_gaze_world' in value:
                    from ..geometry import quat_to_matrix
                    optical = self._numpy(moving_camera.data.quat_w_ros)[0]
                    forward = quat_to_matrix(optical)[:, 2]
                    desired = gaze_path[-1]-eye_path[-1]
                    desired /= np.linalg.norm(desired)
                    if np.linalg.norm(forward-desired) > .001:
                        raise RuntimeError('inspection camera aim readback failed; no retry')
                self._inspection_gaze = gaze_path[-1].copy()
            arrived = (np.linalg.norm(error[:3]) <= .003 and np.linalg.norm(error[3:]) <= .03
                       and (not (smooth_path is not None or open_arrival) or stable_steps >= 4))
            receipt = ExecutionReceipt(command_id, before.key, self.current.key, value['max_steps'], completed,
                'executed', ('contact tracking guard stopped motion' if contact_stopped else
                             'transit waypoint passed' if waypoint_passed else
                             'local stage arrived' if arrived else 'local stage budget ended without arrival'),
                'sensor_local_diffik', completed*before.control_dt, time.monotonic()-started,
                float(np.linalg.norm(error[:3])), float(np.linalg.norm(error[3:])))
            if self.record_episode is not None:
                with (self.record_episode/'local_stages.jsonl').open('a') as stream:
                    stream.write(__import__('json').dumps({'command_id': command_id, 'request': value,
                        'receipt': receipt.to_dict(), 'unknown_clearance': True,
                        'contact_tracking_stopped': contact_stopped,
                        'camera_path_world': None if eye_path is None else eye_path.tolist(),
                        'camera_gaze_path_world': None if eye_path is None else gaze_path.tolist(),
                        'camera_eye_error_m': None if eye_path is None else float(camera_error)})+'\n')
            if waypoint_passed:
                self._transit_context = dict(observation_id=self.current.key,target=target.copy(),
                    feedback=feedback,solver=solver,opening=value['gripper_open'])
            return StepResult(self.current, receipt, self._evaluation)
        except Exception as exc:
            self._poisoned = True
            if self.record_episode is not None:
                with (self.record_episode/'local_stages.jsonl').open('a') as stream:
                    stream.write(__import__('json').dumps({'command_id': command_id, 'request': value,
                        'confirmed_actions': completed, 'halted': True,
                        'error': f'{type(exc).__name__}: {exc}', 'never_retry': True})+'\n')
            raise AmbiguousExecution(f'local stage stopped after {completed} confirmed actions; never retry') from exc

    def fk_preview(self, joints, names):
        if tuple(names) != self.joint_names: raise InputRejected("FK joint order mismatch")
        a = np.asarray(joints, dtype=float)
        if a.ndim != 2 or a.shape[1] != 7 or not 1 <= len(a) <= 64 or not np.isfinite(a).all():
            raise InputRejected("FK needs a finite Hx7 robot joint array")
        return np.stack([self.kin.fk(q, self.base_pose) for q in a])

    def evaluate(self): return self._evaluation

    def metadata(self):
        scfg = self.sim.env.scene.cfg
        return {"backend": "embodiedswe", "robot": "franka", "preset": self.task_config["preset"],
                "task_instruction": self.task_config["instruction"], "control_dt": 1/self.sim.rate_hz,
                "controller": "joint PD; direct EEF via robot-only DLS IK",
                "controller_qualification": "GPU execution not validated by package author",
                "time_model": "physics_paused_during_inference", "privileged_policy_inputs": False,
                "depth_recording": bool(getattr(self, "record_depth", False)),
                "depth_policy_input": False,
                "wrist_target_hand": self.task_config.get('wrist_target_hand'),
                "local_stages_enabled": bool(getattr(self, 'allow_local_stages', False)),
                "continuous_transit_enabled": True,
                "open_stage_settling": "four_stable_pose_and_aperture_samples; closure_dwell_unchanged",
                "position_integral_antiwindup": "opposing_axis_reset_above_1mm",
                "trajectory_feedforward": "one_step_world_increment_optional",
                "local_motion_profiles": {"conservative": {"linear_m_s": .0225, "angular_rad_s": .06},
                    "elevated_open_2x": {"linear_m_s": .045, "angular_rad_s": .12,
                                         "qualification": "experimental; not contact or payload qualified"},
                    "elevated_open_5x": {"linear_m_s": .1125, "angular_rad_s": .30, "trajectory": "quintic_rest_to_rest", "qualification": "experimental"},
                    "elevated_open_10x": {"linear_m_s": .225, "angular_rad_s": .60, "trajectory": "quintic_rest_to_rest", "qualification": "experimental"}},
                "local_stage_rotation_integral": bool(getattr(self, 'local_stage_rotation_integral', False)),
                "inspection_camera_enabled": bool(getattr(self, 'allow_inspection_camera', False)),
                "inspection_camera_gaze_enabled": bool(getattr(self, 'allow_inspection_camera', False)),
                "contact_tracking_guard_enabled": bool(getattr(self, 'allow_local_stages', False)),
                "inspection_camera_qualification": "idealized sensor only; no collision body or hardware clearance",
                "last_gripper_command": getattr(self, '_last_gripper_command', None),
                "local_stage_qualification": "experimental native DiffIK through joint tracker; see local-stage evidence, contact/payload not qualified",
                "real_hardware_supported": False, "camera_map": self.camera_map,
                "grasp_weld": getattr(scfg, "grasp_weld", "not_declared"),
                "physics_assists": "upstream scene defaults preserved; inspect grasp_weld and SOURCE_AUDIT",
                "worker_id": getattr(self,"worker_id",None),
                "record_root": str(self.record_root) if self.record_root else None}

    def close(self): self.sim.close()
