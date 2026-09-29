import numpy as np
import pytest
from physical_exec.depth import surface_point


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
