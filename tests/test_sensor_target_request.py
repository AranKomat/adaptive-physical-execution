import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('measurement_id,accepted',[('e:12',True),('e:11',False)])
def test_feature_feedback_requires_current_measurements(tmp_path,measurement_id,accepted):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id':'e:12'}))
    for role in ('left','right','wrist'):
        (tmp_path/f'{role}.png').write_bytes(b'fixture-only')
    measurements=tmp_path/'measurements.json'
    measurements.write_text(json.dumps({'observation_id':measurement_id,'connector':{'samples':[]}}))
    output=tmp_path/'messages.json'
    script=Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    result=subprocess.run([sys.executable,str(script),'--stage','feature_inventory',
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
        (tmp_path/f'{role}.png').write_bytes(b'fixture-only-no-model-call')
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
        (tmp_path/f'{role}.png').write_bytes(b'fixture-only-no-model-call')
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
        (tmp_path/f'{role}.png').write_bytes(b'fixture-only-no-model-call')
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
@pytest.mark.parametrize('stage',['feature_inventory','correspondence','inspection_camera'])
def test_feature_inventory_carry_identity_history(tmp_path,old_id,accepted,stage):
    current, old = tmp_path/'current', tmp_path/'old'
    for path, obs in ((current,'e:12'),(old,old_id)):
        path.mkdir()
        (path/'state.json').write_text(json.dumps({'observation_id':obs}))
        for role in ('left','right','wrist'):
            (path/f'{role}.png').write_bytes(b'fixture-only-no-model-call')
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
            (path/f'{role}.png').write_bytes(b'fixture-only-no-model-call')
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
