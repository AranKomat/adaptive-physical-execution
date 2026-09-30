import json

import numpy as np
import pytest

from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment
from physical_exec.backends.fixture import FixtureEnvironment
from physical_exec.errors import InputRejected
from physical_exec.transport import EnvironmentService


def test_depth_query_is_bounded_and_read_only():
    env = FixtureEnvironment()
    calls = []
    env.depth_points = lambda obs, samples: calls.append((obs.key,samples)) or {'samples': []}
    service = EnvironmentService(env)
    service.dispatch('/reset', {'seed': 0})
    obs = service.observation
    camera=next(iter(obs.images))
    payload = dict(observation_id=obs.key,samples=[dict(camera=camera,pixel_uv=[2,2])])
    service.dispatch('/depth-points',payload)
    assert service.observation is obs and len(calls)==1 and not service.commands
    for change in ({'observation_id':'stale'}, {'samples':[]},
                   {'samples':payload['samples']*7},
                   {'samples':[dict(camera='../../secret',pixel_uv=[2,2])]},
                   {'samples':[dict(camera=camera,pixel_uv=[True,2])]},
                   {'hidden_pose':True}):
        with pytest.raises(InputRejected):
            service.dispatch('/depth-points',{**payload,**change})
    assert len(calls)==1


def test_backend_reads_only_current_depth(tmp_path,observation):
    env=EmbodiedSWEEnvironment.__new__(EmbodiedSWEEnvironment)
    env.record_depth=True
    env.record_episode=tmp_path
    env.current=observation
    base=tmp_path/'wrist_depth'
    base.mkdir()
    stem=f'{observation.seq:06d}'
    calibration=dict(observation_id=observation.key,depth_convention='camera_optical_z',
        depth_units='meters',intrinsic_matrix=[[100,0,2],[0,100,2],[0,0,1]],
        camera_quaternion_world_wxyz_optical=[1,0,0,0],camera_position_world=[0,0,0])
    (base/f'{stem}.json').write_text(json.dumps(calibration))
    np.save(base/f'{stem}.npy',np.full((5,5),.2))
    value=env.depth_points(observation,[dict(camera='wrist',pixel_uv=[2,2])])
    assert value['samples'][0]['status']=='measured'
    assert value['observation_id']==observation.key
    np.save(base/f'{stem}.npy',np.full((5,5),np.nan))
    value=env.depth_points(observation,[dict(camera='wrist',pixel_uv=[2,2])])
    assert value['samples'][0]['status']=='rejected'
    assert 'measurement' not in value['samples'][0]
    calibration['observation_id']='stale'
    (base/f'{stem}.json').write_text(json.dumps(calibration))
    with pytest.raises(InputRejected,match='stale'):
        env.depth_points(observation,[dict(camera='wrist',pixel_uv=[2,2])])


def test_direct_query_then_action_budget_and_freshness(tmp_path):
    from dataclasses import replace
    from physical_exec.backends.fixture import FixtureProvider
    from physical_exec.runner import run_episode, RunBudget
    from physical_exec.trace import verify_trace
    from test_runner_transport import controller

    class Env(FixtureEnvironment):
        queries=0
        def metadata(self):
            return {**super().metadata(),'depth_point_query_available':True}
        def depth_points(self,obs,samples):
            self.queries+=1
            return dict(observation_id=obs.key,samples=[])
    class Provider(FixtureProvider):
        def act(self,instructions,messages,schema,timeout_seconds=None):
            reply=super().act(instructions,messages,schema,timeout_seconds)
            has_feedback='CURRENT SENSOR DEPTH MEASUREMENTS' in str(messages)
            assert has_feedback == (self.calls==2)
            raw=reply.arguments.copy()
            if self.calls==1:
                raw.update(decision_type='measure_depth',actions=[],
                           samples=[dict(camera=schema['properties']['samples']['items']['properties']['camera']['enum'][0],pixel_uv=[2,2])])
            else:
                raw.update(decision_type='act',samples=[])
            return replace(reply,arguments=raw)
    env=Env(complete_after=100)
    ctrl=controller(provider=Provider())
    out=run_episode(env,ctrl,tmp_path/'depth',0,RunBudget(3,50,60),depth_queries=True)
    result=json.loads((out/'result.json').read_text())
    assert result['decision_count']==3 and result['executed_control_steps']==6
    assert env.queries==1
    assert result['terminal_reason']=='decision_budget'
    assert ctrl.memory.config.image_layout=='separate'
    assert verify_trace(out)['images_checked']


def test_repeated_queries_end_with_stop_option(tmp_path):
    from dataclasses import replace
    from physical_exec.backends.fixture import FixtureProvider
    from physical_exec.runner import run_episode,RunBudget
    from test_runner_transport import controller
    class Env(FixtureEnvironment):
        def metadata(self):
            return {**super().metadata(),'depth_point_query_available':True}
        def depth_points(self,obs,samples):
            return dict(observation_id=obs.key,samples=[dict(status='measured')])
    class Provider(FixtureProvider):
        def act(self,instructions,messages,schema,timeout_seconds=None):
            reply=super().act(instructions,messages,schema,timeout_seconds)
            raw=reply.arguments.copy()
            if self.calls <= 2:
                raw.update(decision_type='measure_depth',actions=[],samples=[dict(
                    camera=schema['properties']['samples']['items']['properties']['camera']['enum'][0],
                    pixel_uv=[2,2])])
            else:
                assert schema['properties']['decision_type']['enum']==['act','stop']
                raw.update(decision_type='stop',actions=[],samples=[])
            return replace(reply,arguments=raw)
    run=run_episode(Env(),controller(provider=Provider()),tmp_path/'run',0,
                    RunBudget(6,30,60),depth_queries=True)
    result=json.loads((run/'result.json').read_text())
    assert result['decision_count']==3 and result['executed_control_steps']==0
    assert result['terminal_reason']=='model_stopped_incomplete'


def test_valid_depth_measurement_disables_second_query(tmp_path):
    from dataclasses import replace
    from physical_exec.backends.fixture import FixtureProvider
    from physical_exec.runner import run_episode, RunBudget
    from test_runner_transport import controller

    class Env(FixtureEnvironment):
        def metadata(self):
            return {**super().metadata(), 'depth_point_query_available': True}

        def depth_points(self, obs, samples):
            return dict(observation_id=obs.key,
                        samples=[dict(status='measured', measurement={'point_hand_m': [0, 0, 0]})])

    class Provider(FixtureProvider):
        def act(self, instructions, messages, schema, timeout_seconds=None):
            reply = super().act(instructions, messages, schema, timeout_seconds)
            raw = reply.arguments.copy()
            if self.calls == 1:
                raw.update(decision_type='measure_depth', actions=[], samples=[dict(
                    camera=schema['properties']['samples']['items']['properties']['camera']['enum'][0],
                    pixel_uv=[2, 2])])
            else:
                assert schema['properties']['decision_type']['enum'] == ['act', 'stop']
                raw.update(decision_type='act', samples=[], actions=[dict(
                    delta_world=[0, 0, 0, 0, 0, 0], gripper_open=1)])
            return replace(reply, arguments=raw)

    run = run_episode(Env(complete_after=100), controller(provider=Provider()), tmp_path/'run', 0,
                      RunBudget(2, 30, 60), depth_queries=True)
    result = json.loads((run/'result.json').read_text())
    assert result['decision_count'] == 2 and result['executed_control_steps'] == 1
