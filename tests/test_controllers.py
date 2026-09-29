from dataclasses import replace
import numpy as np
import pytest
from physical_exec.backends.fixture import FixtureProvider,FixtureProposer
from physical_exec.controllers.ports import ControllerPort,Proposal,validate_schema,hybrid_schema
from physical_exec.memory import ExecutionMemory,MemoryConfig
from physical_exec.contracts import Usage,ActionChunk
from physical_exec.providers.responses import ModelReply
from physical_exec.errors import InputRejected
from physical_exec.safety import Limits,validate_chunk


def build(mode,provider=None,proposer=None):
    return ControllerPort(mode,provider or FixtureProvider(),ExecutionMemory(MemoryConfig()),Limits(),3,
                          proposer or (FixtureProposer() if mode=='hybrid' else None))

@pytest.mark.parametrize('mode',['direct_roboicl','direct_reference','hybrid'])
def test_ports_make_valid_actions(observation,mode):
    ctrl=build(mode);d=ctrl.decide(observation)
    a=validate_chunk(d.action,observation,Limits())
    assert len(a.values)==3
    assert a.kind==('joint_absolute' if mode=='hybrid' else 'eef_absolute_world')


def test_hybrid_prompt_distinguishes_command_domains_and_progress(observation):
    class Inspect(FixtureProvider):
        def act(self, instructions, *args, **kwargs):
            assert 'For EEF commands' in instructions
            assert 'per-joint target-step limit' in instructions
            assert 'FK previews are not EEF commands' in instructions
            assert 'Robot motion alone is not task progress' in instructions
            return super().act(instructions, *args, **kwargs)
    build('hybrid', Inspect()).decide(observation)


def test_franka_contact_geometry_is_robot_relative(observation):
    class Inspect(FixtureProvider):
        def act(self, instructions, *args, **kwargs):
            assert 'hand-local +z, NOT world +z' in instructions
            assert 'not an object pose or contact measurement' in instructions
            from physical_exec.geometry import pose_matrix
            from physical_exec.trace import dumps
            expected = (pose_matrix(obs.eef_pose) @ np.array([0,0,.1034,1]))[:3]
            assert dumps(expected.tolist()) in instructions
            return super().act(instructions, *args, **kwargs)
    obs = replace(observation, robot='franka', eef_frame='panda_hand')
    build('hybrid', Inspect()).decide(obs)


def gate_raw(obs,p,mode='eef',status='uncertain',intent='uncertain'):
    return {'observation_id':obs.key,'proposal_id':p.action.proposal_id,'mode':mode,'execute_steps':1,
            'assessment':{'execution_status':status,'intent_status':intent,'evidence':'visual report'},
            'reason':'test','translation_world':[0,0,0],'rotation_world':[0,0,0],
            'gripper_override':'keep','actions':[{'pose_world_xyz_wxyz':obs.eef_pose.tolist(),'gripper_open':.7}]}


def test_hybrid_gate_rejects_uncertainty_only(observation):
    c=build('hybrid');p=FixtureProposer().propose(observation)
    with pytest.raises(InputRejected):c._hybrid_action(gate_raw(observation,p),observation,p)
    a=c._hybrid_action(gate_raw(observation,p,status='failed'),observation,p)
    assert a.kind=='eef_absolute_world'


def test_hybrid_accept_cannot_hide_edits(observation):
    c=build('hybrid');p=FixtureProposer().propose(observation)
    r=gate_raw(observation,p,mode='accept');r['actions']=[]
    r['translation_world']=[.001,0,0]
    with pytest.raises(InputRejected):c._hybrid_action(r,observation,p)
    r['translation_world']=[0,0,0]
    assert len(c._hybrid_action(r,observation,p).values)==1


def test_hybrid_edit_uses_robot_only_fk(observation):
    c=build('hybrid');p=FixtureProposer().propose(observation)
    r=gate_raw(observation,p,mode='edit',intent='misaligned');r['actions']=[];r['translation_world']=[0,.01,0]
    a=c._hybrid_action(r,observation,p)
    assert a.values[0,1]==pytest.approx(.01)
    assert 'no object states' in p.public()['notice']


def test_stale_model_observation_and_boolean_numbers(observation):
    class Bad(FixtureProvider):
        def act(self,*a,**k):
            r=super().act(*a,**k);r.arguments['observation_id']='old';return r
    with pytest.raises(InputRejected):build('direct_roboicl',Bad()).decide(observation)
    with pytest.raises(InputRejected):validate_schema(True,{'type':'number'})
    with pytest.raises(InputRejected):validate_schema({'extra':1},{'type':'object','properties':{},'required':[]})
