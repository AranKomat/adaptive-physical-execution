import numpy as np
import pytest

from physical_exec.geometry import pose_error, rotvec_to_quat
from physical_exec.transit_trajectory import transit_trajectory


@pytest.mark.parametrize('scale', [5, 10])
def test_transit_bounds_endpoints_and_discrete_acceleration(scale):
    start = [0,0,.4,1,0,0,0]
    end = np.r_[.3,0,.4,rotvec_to_quat([0,0,1.57])]
    result = transit_trajectory(start,end,speed_scale=scale)
    poses = result['poses']
    assert np.linalg.norm(pose_error(poses[0],start)) < 1e-10
    assert np.linalg.norm(pose_error(poses[-1],end)) < 1e-10
    velocity = np.array([pose_error(a,b)*15 for a,b in zip(poses[:-1],poses[1:])])
    acceleration = np.diff(np.vstack([np.zeros(6),velocity,np.zeros(6)]),axis=0)*15
    assert np.max(np.linalg.norm(velocity[:,:3],axis=1)) <= .0225*scale+1e-10
    assert np.max(np.linalg.norm(velocity[:,3:],axis=1)) <= .06*scale+1e-10
    assert np.max(np.linalg.norm(acceleration[:,:3],axis=1)) <= .45+1e-10
    assert np.max(np.linalg.norm(acceleration[:,3:],axis=1)) <= 1.2+1e-10
    assert np.all(np.diff(poses[:,0]) >= 0)


@pytest.mark.parametrize('kwargs', [dict(speed_scale=20),dict(speed_scale=True),
    dict(speed_scale=5,dt=float('nan')),dict(speed_scale=10,linear_acceleration=0)])
def test_invalid_profile_rejected(kwargs):
    with pytest.raises(ValueError):
        transit_trajectory([0,0,.4,1,0,0,0],[0,0,.5,1,0,0,0],**kwargs)


def test_ten_x_30cm_includes_acceleration_not_cruise_only_estimate():
    result = transit_trajectory([0,0,.4,1,0,0,0],[.3,0,.4,1,0,0,0],speed_scale=10)
    assert 2.5 <= result['duration_seconds'] < 2.6
