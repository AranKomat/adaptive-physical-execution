import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pytest


def invoke(tmp_path, monkeypatch, previous_episode='e', response_id='e:10',
           decision='carry_above_slot', calibration_id='e:10', reuse=False):
    source = Path(__file__).resolve().parents[1]/'scripts/plan_sensor_carry.py'
    spec = importlib.util.spec_from_file_location('carry_test',source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = dict(observation_id='e:10',hand_pose_world=[.2,-.34,.45,0,0,1,0])
    (tmp_path/'state.json').write_text(json.dumps(state))
    for role, origin, depth in [('left',[.25,-.35,.45],.2),('right',[.5,0,.3],.27)]:
        np.save(tmp_path/f'{role}_depth.npy',np.full((5,5),depth))
        calibration = dict(observation_id=calibration_id,depth_convention='camera_optical_z',depth_units='meters',
                           intrinsic_matrix=[[100,0,2],[0,100,2],[0,0,1]],camera_position_world=origin,
                           camera_quaternion_world_wxyz_optical=[0,1,0,0])
        (tmp_path/f'{role}_calibration.json').write_text(json.dumps(calibration))
    response = dict(observation_id=response_id,decision=decision,
                    held_feature=dict(camera='left',pixel_uv=[2,2]),slot_feature=dict(camera='right',pixel_uv=[2,2]))
    (tmp_path/'response.json').write_text(json.dumps(response))
    previous = dict(observation_id=previous_episode+':0',phases=[dict(hand_pose_world=state['hand_pose_world'])])
    (tmp_path/'previous.json').write_text(json.dumps(previous))
    monkeypatch.setattr(sys,'argv',[str(source),'--capture',str(tmp_path),'--response',str(tmp_path/'response.json'),
                                  '--previous-command',str(tmp_path/'previous.json'),'--output',str(tmp_path/'plan.json')]
                                  + (['--reuse-pixel-template'] if reuse else []))
    module.main()
    return json.loads((tmp_path/'plan.json').read_text())


def test_carry_is_elevated_relative_translation(tmp_path,monkeypatch):
    plan = invoke(tmp_path,monkeypatch)
    assert not plan['finish']
    final = plan['phases'][-1]['hand_pose_world']
    np.testing.assert_allclose(final,[.45,.01,.46,0,0,1,0])
    assert all(p['hand_pose_world'][2] >= .45 and p['actions'] <= 180 for p in plan['phases'])


def test_previous_command_must_match_episode(tmp_path,monkeypatch):
    with pytest.raises(ValueError,match='another episode'):
        invoke(tmp_path,monkeypatch,'other')


def test_cached_selection_is_explicit_and_remeasured(tmp_path, monkeypatch):
    result = invoke(tmp_path, monkeypatch, response_id='old:1', reuse=True)
    assert result['selector_observation_id'] == 'old:1'
    assert result['observation_id'] == 'e:10'
    assert result['target_source'].startswith('cached Astra pixel template')
    assert result['measurements']['slot_feature']['observation_id'] == 'e:10'


@pytest.mark.parametrize('overrides', [
    {'response_id': 'e:9'}, {'decision': 'inspect'}, {'decision': 'stop'},
    {'calibration_id': 'e:9'},
])
def test_carry_rejects_stale_or_unapproved_selection(tmp_path, monkeypatch, overrides):
    with pytest.raises(ValueError):
        invoke(tmp_path, monkeypatch, **overrides)
    assert not (tmp_path/'plan.json').exists()
