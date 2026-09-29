"""Unit tests with dependency-injected test doubles, NOT Isaac/GPU validation."""
from types import SimpleNamespace
from dataclasses import replace
import numpy as np
import pytest
from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment
from physical_exec.contracts import ActionChunk
from physical_exec.errors import InputRejected
from physical_exec.kinematics import IKResult
from physical_exec.safety import Limits

class FakeKin:
    limits=np.array([[-2,2]]*7)
    def fk(self,q,base_pose=None):return np.array([.4+q[0],q[1],.4+q[2],1,0,0,0])
    def solve(self,target,q,base_pose=None):
        target_q=q.copy();target_q[:3]=np.array(target[:3])-[.4,0,.4]
        return IKResult(target_q,True,0,0,1)


def make_bridge(observation):
    b=EmbodiedSWEEnvironment.__new__(EmbodiedSWEEnvironment)
    b.current=observation;b.raw=None;b.seq=0;b.episode_id=observation.episode_id
    b.limits=Limits();b.kin=FakeKin();b.base_pose=np.array([0,0,0,1,0,0,0]);b.joint_names=observation.joint_names
    b.camera_map={k:k for k in observation.images};b.task_config={'instruction':observation.task}
    b.record_episode=None;b._poisoned=False
    q=observation.joints.copy();closed=1-observation.gripper_open;calls=[]
    def raw():
        return {'images':{k:v[None] for k,v in observation.images.items()},'state':np.r_[q,closed][None],
                'success':np.array([False]),'progress':np.array([.75]),'secret_object_pose':'DO_NOT_EXPOSE'}
    def step(a):
        nonlocal q,closed
        calls.append(a.copy());q=a[0,:7].copy();closed=float(a[0,-1]);return raw()
    b.sim=SimpleNamespace(step=step,rate_hz=15)
    b._measured_eef=lambda:b.kin.fk(q)
    return b,calls,raw


def test_extract_is_allowlist_with_real_gripper_conversion(observation):
    b,calls,raw=make_bridge(observation)
    o=b._extract(raw())
    assert o.gripper_open==pytest.approx(.7)
    assert 'secret_object_pose' not in o.public_state()
    assert b.evaluate().score==pytest.approx(.75)


def test_joint_dispatch_to_upstream_closedness(observation):
    b,calls,_=make_bridge(observation)
    values=np.repeat(np.r_[observation.joints,.2][None],2,axis=0)
    values[:,0]=[.01,.02]
    action=ActionChunk('joint_absolute',values,observation.key,observation.control_dt,'test',observation.joint_names)
    result=b.step(action,'cmd')
    assert len(calls)==2 and result.receipt.executed_steps==2
    assert calls[0][0,-1]==pytest.approx(.8)
    assert result.observation.gripper_open==pytest.approx(.2)
    assert result.evaluation.native


def test_bad_joint_or_ik_never_executes(observation):
    b,calls,_=make_bridge(observation)
    a=ActionChunk('joint_absolute',np.r_[[1,0,0,0,0,0,0],.7][None],observation.key,observation.control_dt,'test',observation.joint_names)
    with pytest.raises(InputRejected):b.step(a,'cmd')
    assert not calls
    b.kin.solve=lambda *a:IKResult(np.zeros(7),False,.4,.2,80)
    a=ActionChunk('eef_delta_world',[[.01,0,0,0,0,0,.5]],observation.key,observation.control_dt,'test')
    with pytest.raises(InputRejected):b.step(a,'cmd2')
    assert not calls


def test_cartesian_dispatch_is_robot_only_ik(observation):
    b,calls,_=make_bridge(observation)
    a=ActionChunk('eef_delta_world',[[.01,0,0,0,0,0,.5]]*2,observation.key,observation.control_dt,'test')
    result=b.step(a,'cmd')
    assert result.observation.seq==2
    assert calls[1][0,0]==pytest.approx(.02)
    assert result.receipt.tracking_position_error_m<1e-7  # native command path is float32
