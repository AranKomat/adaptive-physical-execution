import base64
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.parametrize('stage', ['socket_gap', 'coarse_centerline'])
def test_gap_review_accepts_native_right_crop(tmp_path, stage):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:12'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080)).save(tmp_path/f'{role}.png')
    output = tmp_path/'messages.json'
    script = Path(__file__).parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable, str(script), '--capture', str(tmp_path),
        '--stage', stage, '--closeup-right', '800', '480', '1280', '570',
        '--output', str(output)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    content = json.loads(output.read_text())[0]['content']
    assert sum(p['type'] == 'image_url' for p in content) == 4
    assert any('800 + displayed_u' in p.get('text', '') for p in content)
    assert '1920x1080' in content[0]['text']
    assert '640x360' not in content[0]['text']


@pytest.mark.parametrize('stage,accepted', [('correspondence', True), ('grasp', False)])
def test_paired_native_crops_preserve_both_feature_mappings(tmp_path, stage, accepted):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:12'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080)).save(tmp_path/f'{role}.png')
    output = tmp_path/'messages.json'
    script = Path(__file__).parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable, str(script), '--capture', str(tmp_path),
        '--stage', stage, '--closeup-left', '320', '350', '650', '570',
        '--closeup-right', '950', '480', '1280', '570', '--output', str(output)],
        capture_output=True, text=True, check=False)
    assert (result.returncode == 0) == accepted
    if not accepted:
        assert not output.exists()
        return
    content = json.loads(output.read_text())[0]['content']
    assert sum(p['type'] == 'image_url' for p in content) == 5
    assert any('320 + displayed_u' in p.get('text', '') for p in content)
    assert any('950 + displayed_u' in p.get('text', '') for p in content)
    for part in content:
        if part['type'] == 'image_url':
            with Image.open(io.BytesIO(base64.b64decode(
                    part['image_url']['url'].split(',', 1)[1]))) as image:
                assert max(image.size) <= 640


@pytest.mark.parametrize('stage,accepted', [('socket_gap', True), ('grasp', False)])
def test_single_pixel_rails_are_explicit_and_observation_only(tmp_path, stage, accepted):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:12'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable, str(script), '--stage', stage,
        '--capture', str(tmp_path), '--output', str(output), '--single-pixel-rails'],
        capture_output=True, text=True)
    assert (result.returncode == 0) == accepted
    if accepted:
        prompt = json.loads(output.read_text())[0]['content'][0]['text']
        assert 'CENTER PIXEL (1x1)' in prompt
        assert 'NOT evidence of accuracy' in prompt
        assert 'does NOT authorize movement' in prompt
    else:
        assert not output.exists()


def test_inspection_camera_does_not_assert_a_fixed_occluder(tmp_path):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:12'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
        (tmp_path/f'{role}_calibration.json').write_text(json.dumps({'observation_id': 'e:12'}))
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    subprocess.run([sys.executable, str(script), '--stage', 'inspection_camera',
                    '--capture', str(tmp_path), '--output', str(output)], check=True)
    prompt = json.loads(output.read_text())[0]['content'][0]['text']
    assert 'Determine from the CURRENT images' in prompt
    assert 'Current right view shows the cooler side' not in prompt


@pytest.mark.parametrize('limit,accepted', [('0.2', True), ('0.25', False), ('nan', False)])
def test_inspection_translation_budget_is_explicit_and_bounded(tmp_path, limit, accepted):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:12'}))
    for role in ('left','right','wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
        (tmp_path/f'{role}_calibration.json').write_text(json.dumps({'observation_id':'e:12'}))
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable, str(script), '--stage', 'inspection_motion',
        '--capture', str(tmp_path), '--output', str(output), '--inspection-motion-limit-m', limit],
        capture_output=True, text=True)
    assert (result.returncode == 0) == accepted
    if accepted:
        assert 'at most 0.20 m' in output.read_text()
        assert 'dz >= 0 (no lowering)' in output.read_text()
    else:
        assert not output.exists()


@pytest.mark.parametrize('measurement_id,accepted',[('e:12',True),('e:11',False)])
@pytest.mark.parametrize('stage', ['feature_inventory', 'grasp', 'socket_gap', 'coarse_centerline'])
def test_feature_feedback_requires_current_measurements(tmp_path,measurement_id,accepted,stage):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id':'e:12'}))
    for role in ('left','right','wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
    measurements=tmp_path/'measurements.json'
    measurements.write_text(json.dumps({'observation_id':measurement_id,'connector':{'samples':[]}}))
    output=tmp_path/'messages.json'
    script=Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result=subprocess.run([sys.executable,str(script),'--stage',stage,
        '--capture',str(tmp_path),'--feature-measurements',str(measurements),'--output',str(output)],
        capture_output=True,text=True)
    assert (result.returncode==0)==accepted
    if accepted:
        assert 'WRONG semantic surface' in output.read_text()
    else:
        assert not output.exists()


@pytest.mark.parametrize('result_id,accepted',[('e:12',True),('e:11',False)])
def test_contact_recovery_uses_current_receipt_not_evaluator(tmp_path,result_id,accepted):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id':'e:12'}))
    for role in ('left','right','wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
    (tmp_path/'evaluator_only.json').write_text('{"hidden":"EVALUATOR_SENTINEL"}')
    receipt=tmp_path/'receipt.json'
    receipt.write_text(json.dumps(dict(resulting_observation_id=result_id,status='executed',
                                      reason='local stage budget ended without arrival')))
    output=tmp_path/'messages.json'
    script=Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result=subprocess.run([sys.executable,str(script),'--stage','contact_recovery','--capture',str(tmp_path),
        '--contact-receipt',str(receipt),'--output',str(output)],capture_output=True,text=True)
    assert (result.returncode==0)==accepted
    if accepted:
        text=output.read_text()
        assert 'EVALUATOR_SENTINEL' not in text
        assert 'No insertion retry is available' in text
    else:
        assert not output.exists()


def test_correspondence_review_is_observation_only(tmp_path):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'e:10'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
    # Evaluator artifacts adjacent to observations must not enter the request.
    (tmp_path/'evaluator_only.json').write_text('{"hidden": "EVALUATOR_SENTINEL"}')
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    subprocess.run([sys.executable, str(script), '--stage', 'correspondence',
                    '--capture', str(tmp_path), '--output', str(output)], check=True)
    content = json.loads(output.read_text())[0]['content']
    assert sum(item['type'] == 'image_url' for item in content) == 3
    assert 'NOT motion authorization' in content[0]['text']
    assert 'end_a' in content[0]['text'] and 'end_b' in content[0]['text']
    assert 'EVALUATOR_SENTINEL' not in output.read_text()


def test_feature_inventory_separates_localization_from_alignment(tmp_path):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id':'e:12'}))
    for role in ('left','right','wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'{role}.png')
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    subprocess.run([sys.executable,str(script),'--stage','feature_inventory',
                    '--capture',str(tmp_path),'--output',str(output)],check=True)
    content = json.loads(output.read_text())[0]['content']
    prompt = content[0]['text']
    assert 'One may be localized even if the other is hidden' in prompt
    assert 'NOT an alignment verdict or motion permission' in prompt
    assert 'NOT required for rough surface/axis localization' in prompt
    assert sum(item['type']=='image_url' for item in content) == 3


@pytest.mark.parametrize('old_id,accepted',[('e:1',True),('other:1',False),('e:12',False)])
@pytest.mark.parametrize('stage',['feature_inventory','correspondence','inspection_camera',
                                  'socket_gap','coarse_centerline'])
def test_feature_inventory_carry_identity_history(tmp_path,old_id,accepted,stage):
    current, old = tmp_path/'current', tmp_path/'old'
    for path, obs in ((current,'e:12'),(old,old_id)):
        path.mkdir()
        (path/'state.json').write_text(json.dumps({'observation_id':obs}))
        for role in ('left','right','wrist'):
            Image.new('RGB', (640, 360)).save(path/f'{role}.png')
            (path/f'{role}_calibration.json').write_text(json.dumps({'observation_id':obs}))
    response = tmp_path/'response.json'
    response.write_text(json.dumps(dict(observation_id=old_id,decision='carry_above_slot',
                                       slot_feature=dict(camera='right',pixel_uv=[20,30]))))
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable,str(script),'--stage',stage,
        '--capture',str(current),'--output',str(output),'--prior-carry-capture',str(old),
        '--prior-carry-response',str(response)],capture_output=True,text=True)
    assert (result.returncode==0) == accepted
    if accepted:
        content = json.loads(output.read_text())[0]['content']
        assert sum(item['type']=='image_url' for item in content)==4
        if stage=='inspection_camera':
            assert 'The arm and gripper will HOLD' in content[0]['text']
            assert '0.512m' in content[0]['text']
        assert 'do not silently switch' in content[-2]['text']
        assert 'NOT a current observation' in content[-2]['text']
    else:
        assert not output.exists()


@pytest.mark.parametrize('old_id,selection_id,decision,accepted', [
    ('e:0', 'e:0', 'localized', True),
    ('other:0', 'other:0', 'localized', False),
    ('e:10', 'e:10', 'localized', False),
    ('e:0', 'e:1', 'localized', False),
    ('e:0', 'e:0', 'inspect', False),
])
def test_historical_socket_context_is_bound_and_labeled(tmp_path, old_id, selection_id, decision, accepted):
    current, old = tmp_path/'current', tmp_path/'old'
    for path, obs in ((current, 'e:10'), (old, old_id)):
        path.mkdir()
        (path/'state.json').write_text(json.dumps({'observation_id': obs}))
        for role in ('left', 'right', 'wrist'):
            Image.new('RGB', (640, 360)).save(path/f'{role}.png')
    response = tmp_path/'response.json'
    response.write_text(json.dumps({'observation_id': selection_id, 'decision': decision,
                                    'center': {'camera': 'right', 'pixel_uv': [10, 20]}}))
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result = subprocess.run([sys.executable, str(script), '--stage', 'alignment',
                             '--capture', str(current), '--output', str(output),
                             '--prior-socket-capture', str(old),
                             '--prior-socket-response', str(response)], capture_output=True, text=True)
    assert (result.returncode == 0) == accepted
    if accepted:
        content = json.loads(output.read_text())[0]['content']
        assert sum(item['type'] == 'image_url' for item in content) == 4
        assert 'HISTORICAL evidence, NOT a current view' in content[-2]['text']
        assert 'does not authorize descent' in content[-2]['text']
    else:
        assert not output.exists()
