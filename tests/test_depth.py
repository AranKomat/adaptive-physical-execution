import numpy as np
import pytest
from physical_exec.depth import surface_point, project_surface_memory


def calibration():
    return dict(depth_convention="camera_optical_z", depth_units="meters",
                intrinsic_matrix=[[100,0,3],[0,100,3],[0,0,1]],
                camera_quaternion_world_wxyz_optical=[1,0,0,0],
                camera_position_world=[1,2,3], observation_id="e:0")


def test_surface_point_uses_optical_z():
    result = surface_point(np.full((7,7),2.), calibration(), [4,3])
    np.testing.assert_allclose(result["surface_point_world_m"], [1.02,2,5])


@pytest.mark.parametrize("bad", [np.inf, np.nan, 0., 3.])
def test_reject_invalid_or_mixed_patch(bad):
    depth = np.ones((7,7)); depth[2,2] = bad
    with pytest.raises(ValueError):
        surface_point(depth, calibration(), [3,3])


def test_reject_fractional_pixel():
    with pytest.raises(ValueError):
        surface_point(np.ones((7,7)), calibration(), [3.1,3])


def test_memory_projection_and_occlusion():
    c = calibration()
    point = surface_point(np.full((7,7),2.),c,[4,3])
    c['observation_id']='e:1'
    result = project_surface_memory(point,c,np.full((7,7),2.))
    assert result['status']=='depth_consistent'
    np.testing.assert_allclose(result['projected_pixel_uv'],[4,3])
    assert project_surface_memory(point,c,np.ones((7,7)))['status']=='depth_inconsistent'
    assert project_surface_memory(point,c,np.full((7,7),np.nan))['status']=='invalid_current_depth'
    point['surface_point_world_m']=[3,2,5]
    assert project_surface_memory(point,c,np.ones((7,7)))['status']=='outside_image'
    point['surface_point_world_m']=[1,2,2]
    assert project_surface_memory(point,c,np.ones((7,7)))['status']=='behind_camera'


@pytest.mark.parametrize('old_id',['e:1','e:2','other:0'])
def test_memory_projection_rejects_invalid_history(old_id):
    c=calibration(); c['observation_id']='e:1'
    with pytest.raises(ValueError):
        project_surface_memory(dict(observation_id=old_id,surface_point_world_m=[1,2,5]),c,np.ones((7,7)))
