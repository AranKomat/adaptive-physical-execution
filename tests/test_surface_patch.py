import numpy as np
import pytest

from physical_exec.depth import surface_patch


def calibration(quaternion):
    return dict(observation_id='e:1', depth_convention='camera_optical_z', depth_units='meters',
                intrinsic_matrix=[[320,0,3],[0,320,3],[0,0,1]],
                camera_position_world=[0,0,0], camera_quaternion_world_wxyz_optical=quaternion)


def test_distinguishes_equally_smooth_top_and_side():
    depth = np.full((7,7), .5)
    top = surface_patch(depth, calibration([1,0,0,0]), [3,3])
    side = surface_patch(depth, calibration([2**-.5,0,2**-.5,0]), [3,3])
    assert top['normal_up_cosine'] == pytest.approx(1)
    assert side['normal_up_cosine'] == pytest.approx(0,abs=1e-10)
    assert top['plane_rms_m'] < 1e-10 and side['plane_rms_m'] < 1e-10
    assert top['plane_sample_count'] == 9


@pytest.mark.parametrize('change', ['discontinuity','nan','outside','radius'])
def test_rejects_unsupported_patch(change):
    depth = np.full((7,7), .5)
    pixel, radius = [3,3], 1
    if change == 'discontinuity': depth[3,3] = .6
    if change == 'nan': depth[3,3] = np.nan
    if change == 'outside': pixel = [0,0]
    if change == 'radius': radius = 0
    with pytest.raises(ValueError):
        surface_patch(depth, calibration([1,0,0,0]), pixel, radius=radius)


def test_planner_skips_nearest_smooth_side_face(tmp_path, monkeypatch):
    import importlib.util
    import json
    from pathlib import Path
    import sys
    path = Path(__file__).resolve().parents[1]/'scripts/plan_sensor_osc.py'
    spec = importlib.util.spec_from_file_location('plane_planner_test', path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:1'}))
    (tmp_path/'right_calibration.json').write_text(json.dumps(calibration([1,0,0,0])))
    np.save(tmp_path/'right_depth.npy', np.full((11,11), .5))
    response = tmp_path/'response.json'
    response.write_text(json.dumps(dict(decision='target', observation_id='e:1', camera='right', pixel_uv=[5,5])))
    visited = []
    def patch(depth, calibration, pixel, **kwargs):
        visited.append(list(pixel))
        return dict(surface_point_world_m=[.3,-.3,.15], pixel_uv=list(map(int,pixel)),
                    normal_up_cosine=.05 if len(visited) == 1 else .99, plane_rms_m=0.)
    monkeypatch.setattr(script, 'surface_patch', patch)
    output = tmp_path/'plan.json'
    monkeypatch.setattr(sys, 'argv', [str(path), '--capture', str(tmp_path), '--response', str(response),
        '--stage', 'approach', '--require-upward-surface', '--output', str(output)])
    script.main()
    result = json.loads(output.read_text())
    assert len(visited) == 2
    assert result['measured_surface']['pixel_uv'] != [5,5]
    assert result['measured_surface']['normal_up_cosine'] == .99
