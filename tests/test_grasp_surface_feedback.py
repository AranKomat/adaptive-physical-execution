import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('surface_feedback',
    Path(__file__).resolve().parents[1]/'scripts/grasp_surface_feedback.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_surface_feedback_binding_and_offsets(tmp_path):
    state = dict(observation_id='e:5',step=5,eef_pose_world_xyz_wxyz=[0,0,0,1,0,0,0])
    base = tmp_path/'wrist_depth'
    base.mkdir()
    calibration = dict(observation_id='e:5',depth_convention='camera_optical_z',
        depth_units='meters',intrinsic_matrix=[[100,0,2],[0,100,2],[0,0,1]],
        camera_quaternion_world_wxyz_optical=[1,0,0,0],camera_position_world=[0,0,0])
    (base/'000005.json').write_text(json.dumps(calibration))
    np.save(base/'000005.npy',np.full((5,5),.2))
    selection = dict(observation_id='e:5',samples=[dict(camera='wrist',pixel_uv=[2,2],surface='test')])
    row = module.measure(state,selection,tmp_path)['samples'][0]
    assert row['status']=='measured'
    np.testing.assert_allclose(row['offset_from_nominal_pinch_hand_m'],[0,0,.0966])
    with pytest.raises(ValueError,match='Stale pixel'):
        module.measure(state,{**selection,'observation_id':'e:4'},tmp_path)
    with pytest.raises(ValueError,match='six'):
        module.measure(state,{**selection,'samples':selection['samples']*7},tmp_path)
    calibration['observation_id']='e:4'
    (base/'000005.json').write_text(json.dumps(calibration))
    with pytest.raises(ValueError,match='Stale calibration'):
        module.measure(state,selection,tmp_path)


def test_invalid_depth_returns_no_coordinate(tmp_path):
    state = dict(observation_id='e:5',step=5,eef_pose_world_xyz_wxyz=[0,0,0,1,0,0,0])
    base = tmp_path/'wrist_depth'
    base.mkdir()
    (base/'000005.json').write_text(json.dumps(dict(observation_id='e:5')))
    np.save(base/'000005.npy',np.full((5,5),np.nan))
    selection = dict(observation_id='e:5',samples=[dict(camera='wrist',pixel_uv=[2,2],surface='test')])
    row=module.measure(state,selection,tmp_path)['samples'][0]
    assert row['status']=='rejected'
    assert 'measurement' not in row and 'offset_from_nominal_pinch_hand_m' not in row
