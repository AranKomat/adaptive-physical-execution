from dataclasses import replace

import numpy as np
import pytest

from physical_exec.local_stage import validate_local_stage
from physical_exec.errors import InputRejected
from physical_exec.backends.fixture import FixtureEnvironment
from physical_exec.transport import EnvironmentService
from physical_exec.contracts import ActionChunk


def request(obs):
    return dict(observation_id=obs.key, hand_pose_world=obs.eef_pose.tolist(),
                gripper_open=1., max_steps=30, target_source='robot-only hold test')


@pytest.mark.parametrize('change', [
    {'observation_id': 'stale'}, {'max_steps': 65}, {'max_steps': 181}, {'max_steps': True},
    {'gripper_open': float('nan')}, {'gripper_open': -1}, {'target_source': ''},
    {'hand_pose_world': [0,0,.4,0,0,0,0]},
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
