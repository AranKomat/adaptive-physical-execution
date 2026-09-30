from dataclasses import replace

import numpy as np
import pytest

from physical_exec.local_stage import validate_local_stage
from physical_exec.errors import InputRejected
from physical_exec.backends.fixture import FixtureEnvironment
from physical_exec.transport import EnvironmentService
from physical_exec.contracts import ActionChunk
from physical_exec.geometry import pose_error, quat_mul, rotvec_to_quat
from physical_exec.osc_reference import ramped_pose_target


def test_pose_ramp_supports_bounded_world_rotation():
    start = np.r_[.1, -.2, .4, rotvec_to_quat([.2, -.4, .1])]
    target = np.r_[start[:3]+[.05, 0, 0],
                   quat_mul(rotvec_to_quat([0, .25, 0]), start[3:])]
    previous = start.copy()
    for step in range(1, 65):
        current = ramped_pose_target(start, target, step, .0015, .004)
        change = pose_error(previous, current)
        assert np.linalg.norm(change[:3]) <= .0015+1e-12
        assert np.linalg.norm(change[3:]) <= .004+1e-12
        previous = current
    assert np.linalg.norm(pose_error(previous, target)) < 1e-12


@pytest.mark.parametrize('step,linear,angular', [(0,.0015,.004), (True,.0015,.004),
                         (1,0,.004), (1,.0015,float('nan')), (1,.0015,.02)])
def test_pose_ramp_rejects_invalid_rates(step, linear, angular):
    pose = [0,0,.4,1,0,0,0]
    with pytest.raises(ValueError):
        ramped_pose_target(pose, pose, step, linear, angular)


def request(obs):
    return dict(observation_id=obs.key, hand_pose_world=obs.eef_pose.tolist(),
                gripper_open=1., max_steps=30, target_source='robot-only hold test')


@pytest.mark.parametrize('change', [
    {'observation_id': 'stale'}, {'max_steps': 65}, {'max_steps': 181}, {'max_steps': True},
    {'gripper_open': float('nan')}, {'gripper_open': -1}, {'target_source': ''},
    {'hand_pose_world': [0,0,.4,0,0,0,0]},
    {'settle_at_end':0},
])
def test_stage_rejects_bad_requests(observation, change):
    obs = replace(observation, eef_pose=np.array([0,0,.4,1,0,0,0]))
    with pytest.raises(InputRejected):
        validate_local_stage({**request(obs), **change}, obs)


def test_stage_bounds_and_no_mutation(observation):
    obs = replace(observation, eef_pose=np.array([0,0,.4,1,0,0,0]))
    value = request(obs)
    assert np.allclose(validate_local_stage(value,obs),obs.eef_pose)
    value['hand_pose_world'][0] = .201
    with pytest.raises(InputRejected):
        validate_local_stage(value,obs)


def test_fast_profile_requires_elevated_open_guarded_state(observation):
    obs = replace(observation, eef_pose=np.array([0,0,.4,1,0,0,0]),
                  gripper_open=1., control_dt=1/15)
    value = {**request(obs), 'motion_profile':'elevated_open_2x', 'contact_tracking_guard':True}
    validate_local_stage(value, obs)
    for change in ({'contact_tracking_guard':False}, {'gripper_open':.05},
                   {'hand_pose_world':[0,0,.29,1,0,0,0]}, {'motion_profile':'unbounded'}):
        with pytest.raises(InputRejected):
            validate_local_stage({**value, **change}, obs)
    for changed_obs in (replace(obs,gripper_open=.7), replace(obs,control_dt=.1),
                        replace(obs,eef_pose=np.array([0,0,.29,1,0,0,0]))):
        with pytest.raises(InputRejected):
            validate_local_stage(value,changed_obs)


def test_double_speed_ramp_halves_time_to_same_target():
    start = np.array([0,0,.4,1,0,0,0])
    target = np.r_[0,0,.46,rotvec_to_quat([0,0,.16])]
    slow = ramped_pose_target(start,target,40,.0015,.004)
    fast = ramped_pose_target(start,target,20,.003,.008)
    np.testing.assert_allclose(fast,slow,atol=1e-12)
    np.testing.assert_allclose(fast,target,atol=1e-12)


def test_camera_stage_is_opt_in_and_preserves_commanded_grip(observation):
    value = {**request(observation), 'camera_eye_world':[.6,-.35,.7],
             'camera_gaze_world':[.45,.03,.035]}
    with pytest.raises(InputRejected, match='not enabled'):
        validate_local_stage(value,observation)
    # Measured aperture is .7, but the existing commanded opening is 1.0.
    validate_local_stage(value,observation,allow_inspection_camera=True,last_gripper_command=1.)
    for previous in (None,.3):
        with pytest.raises(InputRejected, match='gripper command'):
            validate_local_stage(value,observation,allow_inspection_camera=True,last_gripper_command=previous)
    moved = {**value,'hand_pose_world':[.41,0,.4,1,0,0,0]}
    with pytest.raises(InputRejected,match='arm hold'):
        validate_local_stage(moved,observation,allow_inspection_camera=True,last_gripper_command=1.)
    with pytest.raises(InputRejected,match='camera eye'):
        validate_local_stage({**value,'camera_eye_world':[float('nan'),0,1]},observation,
                             allow_inspection_camera=True,last_gripper_command=1.)


def test_stage_rpc_requires_opt_in():
    env = FixtureEnvironment()
    service = EnvironmentService(env)
    service.dispatch('/reset', {'seed': 0})
    with pytest.raises(InputRejected, match='not enabled'):
        service.dispatch('/local-stage', {'command_id':'stage', 'action':request(env._observe())})
    assert env.seq == 0


def test_stage_rpc_deduplicates_and_rejects_changed_request():
    class StageDouble(FixtureEnvironment):
        allow_local_stages = True
        calls = 0
        def local_stage(self, value, cid):
            self.calls += 1
            obs = self._observe()
            action = ActionChunk('eef_delta_world', [[0,0,0,0,0,0,1]], obs.key, obs.control_dt, 'TEST_STAGE')
            return self.step(action, cid)
    env = StageDouble()
    service = EnvironmentService(env)
    service.dispatch('/reset', {'seed':0})
    envelope = {'command_id':'stage', 'action':request(env._observe())}
    first = service.dispatch('/local-stage', envelope)
    assert service.dispatch('/local-stage', envelope) == first
    assert env.calls == 1 and env.seq == 1
    changed = {**envelope, 'action':{**envelope['action'], 'max_steps':31}}
    with pytest.raises(InputRejected, match='reuse'):
        service.dispatch('/local-stage', changed)
