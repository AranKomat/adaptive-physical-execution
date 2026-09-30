import base64
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.parametrize('width,height', [(640, 360), (1920, 1080)])
def test_review_bounds_images_and_declares_native_coordinates(tmp_path, width, height):
    (tmp_path/'declared_sequence.json').write_text(json.dumps([{'name': 'descend'}]))
    (tmp_path/'00_observation.json').write_text(json.dumps({'observation_id': 'e:10'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (width, height)).save(tmp_path/f'00_{role}.png')
    output = tmp_path/'messages.json'
    subprocess.run([sys.executable, str(Path(__file__).parents[1]/
        'scripts/prepare_preclosure_review.py'), '--correction', str(tmp_path),
        '--index', '0', '--output', str(output)], check=True)
    content = json.loads(output.read_text())[0]['content']
    assert 'ORIGINAL sensor pixel' in content[0]['text']
    assert sum(p['type'] == 'image_url' for p in content) == 3
    assert any(f'{width}x{height}' in p.get('text', '') for p in content)
    for part in content:
        if part['type'] == 'image_url':
            pixels = base64.b64decode(part['image_url']['url'].split(',', 1)[1])
            with Image.open(io.BytesIO(pixels)) as image:
                assert image.size == (640, 360)


def test_native_crop_retains_mapping_and_rejects_outside_image(tmp_path):
    (tmp_path/'declared_sequence.json').write_text(json.dumps([{'name': 'descend'}]))
    (tmp_path/'00_observation.json').write_text(json.dumps({'observation_id': 'e:10'}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080)).save(tmp_path/f'00_{role}.png')
    output = tmp_path/'messages.json'
    command = [sys.executable, str(Path(__file__).parents[1]/
        'scripts/prepare_preclosure_review.py'), '--correction', str(tmp_path),
        '--index', '0', '--output', str(output), '--closeup-right']
    subprocess.run(command+['800', '500', '1400', '1000'], check=True)
    content = json.loads(output.read_text())[0]['content']
    assert sum(p['type'] == 'image_url' for p in content) == 4
    assert any('800 + displayed_u' in p.get('text', '') for p in content)
    output.unlink()
    result = subprocess.run(command+['800', '500', '2000', '1000'], capture_output=True, check=False)
    assert result.returncode != 0
    assert not output.exists()


@pytest.mark.parametrize('opening,result_id,accepted', [(1., 'e:20', True),
                                                       (.3, 'e:20', False),
                                                       (1., 'e:19', False)])
def test_inspection_review_requires_open_hand_and_matching_receipt(
        tmp_path, opening, result_id, accepted):
    (tmp_path/'after.json').write_text(json.dumps({'observation_id': 'e:20'}))
    (tmp_path/'receipt.json').write_text(json.dumps({
        'observation_id': 'e:10', 'resulting_observation_id': result_id,
        'reason': 'local stage arrived'}))
    (tmp_path/'request.json').write_text(json.dumps({'action': {
        'observation_id': 'e:10', 'gripper_open': opening, 'camera_eye_world': [.3, -.6, .4]}}))
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (640, 360)).save(tmp_path/f'after_{role}.png')
    output = tmp_path/'messages.json'
    result = subprocess.run([sys.executable, str(Path(__file__).parents[1]/
        'scripts/prepare_preclosure_review.py'), '--inspection-probe', str(tmp_path),
        '--output', str(output)], capture_output=True, check=False)
    assert (result.returncode == 0) == accepted
    assert output.exists() == accepted
