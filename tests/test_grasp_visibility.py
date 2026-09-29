import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('grasp_visibility',
    Path(__file__).resolve().parents[1]/'scripts/audit_grasp_visibility.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('z,status', [(1,'surface_consistent'),(.9,'in_front_of_surface'),
                                      (1.1,'occluded'),(-1,'behind_camera')])
def test_depth_visibility_is_not_clearance(z,status):
    calibration = dict(depth_convention='camera_optical_z',depth_units='meters',
        camera_quaternion_world_wxyz_optical=[1,0,0,0],camera_position_world=[0,0,0],
        intrinsic_matrix=[[10,0,5],[0,10,5],[0,0,1]])
    result = module.classify(np.array([0,0,z]),np.ones((11,11)),calibration)
    assert result['status'] == status


def test_discontinuity_stays_unknown():
    calibration = dict(depth_convention='camera_optical_z',depth_units='meters',
        camera_quaternion_world_wxyz_optical=[1,0,0,0],camera_position_world=[0,0,0],
        intrinsic_matrix=[[10,0,5],[0,10,5],[0,0,1]])
    depth = np.ones((11,11))
    depth[5,5] = .5
    assert module.classify(np.array([0,0,1]),depth,calibration)['status'] == 'depth_edge'
