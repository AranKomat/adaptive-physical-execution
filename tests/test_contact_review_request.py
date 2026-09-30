import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image


@pytest.mark.parametrize('fault', [None, 'stale', 'large_gap', 'invalid_crop'])
def test_contact_review_is_current_bounded_and_not_insertion(tmp_path, fault):
    key = 'e:1'
    (tmp_path/'state.json').write_text(json.dumps({
        'observation_id': key, 'hand_pose_world': [.42, 0., .25, 1., 0., 0., 0.]}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080)).save(tmp_path/f'{role}.png')

    def sample(point):
        return {'measurement': {
            'observation_id': key, 'surface_point_world_m': point,
            'local_depth_spread_m': .001, 'neighborhood_radius_pixels': 1}}

    top = .17 if fault == 'large_gap' else .09
    measurements = {'observation_id': 'e:0' if fault == 'stale' else key,
        'connector': {'samples': [sample([.4, 0., top]), sample([.45, 0., top])]},
        'socket': {'samples': [sample([.4, .01, .03]), sample([.45, .01, .03])]}}
    path = tmp_path/'measurements.json'
    path.write_text(json.dumps(measurements))
    output = tmp_path/'messages.json'
    script = Path(__file__).parents[1]/'scripts/prepare_coarse_approach_review.py'
    x1 = '1921' if fault == 'invalid_crop' else '1280'
    result = subprocess.run([sys.executable, str(script), '--capture', str(tmp_path),
        '--measurements', str(path), '--contact-hypothesis', '--closeup-right',
        '970', '390', x1, '570', '--output', str(output)],
        capture_output=True, text=True, check=False)
    assert (result.returncode == 0) == (fault is None), result.stderr
    if fault is not None:
        assert not output.exists()
        return
    content = json.loads(output.read_text())[0]['content']
    prompt = content[0]['text']
    assert 'approve_contact_hypothesis' in prompt
    assert 'not verified keyed insertion' in prompt
    assert 'no measurable recess' in prompt
    assert 'automatic retry or release' in prompt
    assert '"contact_tracking_guard": true' in prompt
    stages = json.loads(prompt.split('\nExact bounded stages: ', 1)[1])
    assert all(stage['contact_tracking_guard'] is True for stage in stages)
    assert '"gripper_open": 0.3' in prompt
    assert sum(p['type'] == 'image_url' for p in content) == 4


@pytest.mark.parametrize('review', [
    {'observation_id': 'e:0', 'decision': 'approve_contact_hypothesis'},
    {'observation_id': 'e:1', 'decision': 'inspect'},
])
def test_contact_executor_rejects_stale_or_denied_review_before_motion(tmp_path, monkeypatch, review):
    script = Path(__file__).parents[1]/'scripts/run_sensor_carry.py'
    spec = importlib.util.spec_from_file_location('contact_runner_test', script)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    calls = []

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def call(self, route):
            calls.append(route)
            if route == '/metadata':
                return {'contact_tracking_guard_enabled': True, 'real_hardware_supported': False,
                        'local_stages_enabled': True, 'continuous_transit_enabled': True}
            assert route == '/observe'

        def close(self):
            pass

    plan = tmp_path/'plan.json'
    plan.write_text('{}')
    path = tmp_path/'review.json'
    path.write_text(json.dumps(review))
    monkeypatch.setattr(runner, 'LocalClient', Client)
    monkeypatch.setattr(runner, 'decode_observation', lambda _: SimpleNamespace(key='e:1'))
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN', 'test-only')
    monkeypatch.setattr(sys, 'argv', [str(script), '--url', 'http://test', '--plan', str(plan),
        '--output', str(tmp_path/'out'), '--exploratory-standoff', '--contact-hypothesis',
        '--contact-review', str(path), '--contact-tracking-guard'])
    with pytest.raises(ValueError, match='fresh explicit approval'):
        runner.main()
    assert calls == ['/metadata', '/observe']


def test_contact_executor_requires_guard_before_reading_plan(tmp_path):
    script = Path(__file__).parents[1]/'scripts/run_sensor_carry.py'
    result = subprocess.run([sys.executable, str(script), '--url', 'http://test',
        '--plan', str(tmp_path/'missing-plan.json'), '--output', str(tmp_path/'out'),
        '--exploratory-standoff', '--contact-hypothesis', '--contact-review',
        str(tmp_path/'missing-review.json')], capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert 'requires --contact-tracking-guard for every segment' in result.stderr
    assert not (tmp_path/'out').exists()
