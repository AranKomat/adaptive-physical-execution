from dataclasses import replace
import numpy as np
import pytest
from physical_exec.contracts import ActionChunk,ExecutionReceipt,Usage
from physical_exec.errors import InputRejected
from physical_exec.safety import Limits,validate_chunk
from physical_exec.backends.flux import droid_arrays,droid_output_to_chunk
from physical_exec.transport import encode_observation,decode_observation
from physical_exec.trace import dumps
import json


def chunk(o,**kw):
    return ActionChunk(**{'kind':'eef_delta_world','values':[[.01,0,0,0,0,0,.7]],
                         'observation_id':o.key,'control_dt':o.control_dt,'source':'test',**kw})

def test_stale_and_time_mismatch(observation):
    for a in [chunk(observation,observation_id='old'),chunk(observation,control_dt=.1)]:
        with pytest.raises(InputRejected): validate_chunk(a,observation,Limits())

def test_euclidean_translation_not_per_axis(observation):
    a=chunk(observation,values=[[.025,.025,0,0,0,0,.7]])
    with pytest.raises(InputRejected): validate_chunk(a,observation,Limits())

def test_delta_conversion_and_workspace(observation):
    out=validate_chunk(chunk(observation),observation,Limits())
    assert out.kind=='eef_absolute_world'
    np.testing.assert_allclose(out.values[0,:3],[.41,0,.4])
    with pytest.raises(InputRejected): validate_chunk(chunk(observation),observation,Limits(workspace_high=(.405,2,3)))

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-0.1,1.1])
def test_invalid_gripper(observation,value):
    with pytest.raises(ValueError): chunk(observation,values=[[0,0,0,0,0,0,value]])

def test_joint_order_continuity_limits(observation):
    a=ActionChunk('joint_absolute',np.r_[np.zeros(7),.5][None],observation.key,observation.control_dt,'test',observation.joint_names)
    validate_chunk(a,observation,Limits(),np.array([[-1,1]]*7))
    with pytest.raises(InputRejected): validate_chunk(replace(a,joint_names=tuple(reversed(a.joint_names))),observation,Limits())
    v=a.values.copy();v[0,0]=.2
    with pytest.raises(InputRejected): validate_chunk(replace(a,values=v),observation,Limits())
    v[0,0]=.1
    with pytest.raises(InputRejected): validate_chunk(replace(a,values=v),observation,Limits(),np.array([[-.05,.05]]*7))

def test_observation_allowlist_and_readonly(observation):
    assert not ({'score','reward','object_pose','success'} & set(observation.public_state()))
    with pytest.raises(ValueError): observation.joints[0]=1
    with pytest.raises(ValueError): observation.images['left'][0,0,0]=4

def test_wire_json_sort_does_not_change_camera_order(observation):
    encoded=json.loads(dumps(encode_observation(observation)))
    restored=decode_observation(encoded)
    assert list(restored.images)==list(observation.images)
    for role in restored.images: np.testing.assert_array_equal(restored.images[role],observation.images[role])

def test_wire_unknown_field_rejected(observation):
    data=encode_observation(observation);data['state']['reward']=1
    with pytest.raises(Exception): decode_observation(data)

def test_droid_adapter_inverts_gripper_and_preserves_joints(observation):
    b=droid_arrays(observation,{'wrist':'wrist','left':'left','right':'right'})
    assert b['images.wrist'].shape==(1,3,360,640)
    assert b['images.wrist'].dtype==np.float32
    assert b['state'][0,-1]==pytest.approx(.3)
    a=droid_output_to_chunk(np.repeat(b['state'][:,None,:],32,axis=1),observation,'test')
    assert a.kind=='joint_absolute';assert a.values.shape==(32,8)
    assert a.values[0,-1]==pytest.approx(.7)

def test_droid_camera_duplication_rejected(observation):
    with pytest.raises(InputRejected): droid_arrays(observation,{'left':'left','right':'left','wrist':'wrist'})
    with pytest.raises(InputRejected): droid_arrays(replace(observation,robot='xarm'),{'left':'left','right':'right','wrist':'wrist'})

def test_receipt_validation():
    with pytest.raises(ValueError): ExecutionReceipt('c','e:0','e:2',1,2,'executed','r','s',1,1)
    with pytest.raises(ValueError): ExecutionReceipt('c','e:0','e:1',1,1,'rejected','r','s',1,1)

def test_usage_no_double_count():
    u=Usage.from_response({'usage':{'input_tokens':1000,'output_tokens':100,
                          'input_tokens_details':{'cached_tokens':900},'output_tokens_details':{'reasoning_tokens':80}}},1)
    assert u.total_tokens==1100 and u.reasoning_tokens==80 and u.usage_reported
    assert not Usage.from_response({},1).usage_reported
