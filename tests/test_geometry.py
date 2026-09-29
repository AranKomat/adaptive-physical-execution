import numpy as np
import pytest
from physical_exec.geometry import (rotvec_to_quat,quat_to_rotvec,quat_mul,quat_to_matrix,matrix_to_quat,
                                    pose_error,pose_matrix,matrix_pose,integrate_world_deltas,unit_quaternion)
from physical_exec.kinematics import URDFKinematics

@pytest.mark.parametrize('rv',[[0,0,0],[1e-10,0,0],[0,0,1.57],[np.pi,0,0],[0,np.pi,0],[0,0,np.pi],[.4,-.7,1.2]])
def test_rotation_roundtrip(rv):
    q=rotvec_to_quat(rv)
    np.testing.assert_allclose(quat_to_matrix(matrix_to_quat(quat_to_matrix(q))),quat_to_matrix(q),atol=1e-8)
    np.testing.assert_allclose(rotvec_to_quat(quat_to_rotvec(q)),q,atol=1e-8)

@pytest.mark.parametrize('q',[[0,0,0,0],[2,0,0,0],[float('nan'),0,0,1]])
def test_bad_quaternion(q):
    with pytest.raises(ValueError): unit_quaternion(q)

def test_world_delta_left_multiplies_and_accumulates():
    initial=np.r_[[.3,.4,.5],rotvec_to_quat([.5,0,0])]
    raw=np.array([[.01,0,0,0,.1,0,.7],[.02,0,0,0,.1,0,.5]])
    result=integrate_world_deltas(initial,raw)
    np.testing.assert_allclose(result[:,0],[.31,.33])
    expected=quat_mul(rotvec_to_quat([0,.2,0]),initial[3:])
    np.testing.assert_allclose(result[-1,3:7],expected,atol=1e-9)
    assert not np.allclose(expected,quat_mul(initial[3:],rotvec_to_quat([0,.2,0])))

def test_pose_roundtrip():
    p=np.r_[[1,2,3],rotvec_to_quat([.2,.4,.6])]
    np.testing.assert_allclose(pose_error(p,matrix_pose(pose_matrix(p))),0,atol=1e-8)

def test_fk_jacobian_finite_difference(urdf_file):
    k=URDFKinematics.from_urdf(urdf_file,'base','tool')
    q=np.array([.2,.1,.3,.2,-.3,.1]); j=k.jacobian(q); fd=np.empty_like(j)
    for i in range(6):
        v=q.copy();v[i]+=1e-6
        fd[:,i]=pose_error(k.fk(q),k.fk(v))/1e-6
    np.testing.assert_allclose(j,fd,atol=1e-5)

def test_ik_reachable_and_unreachable(urdf_file):
    k=URDFKinematics.from_urdf(urdf_file,'base','tool')
    target=k.fk([.3,.1,.2,.1,-.1,.2]); result=k.solve(target,np.zeros(6))
    assert result.converged
    assert result.position_error_m<.002 and result.rotation_error_rad<.02
    target[0]=10
    assert not k.solve(target,np.zeros(6),iterations=15).converged

def test_urdf_rejects_entities_and_missing_chain(tmp_path,urdf_file):
    p=tmp_path/'bad.urdf';p.write_text('<!DOCTYPE robot><robot/>')
    with pytest.raises(ValueError): URDFKinematics.from_urdf(p)
    with pytest.raises(ValueError): URDFKinematics.from_urdf(urdf_file,'wrong','tool')
