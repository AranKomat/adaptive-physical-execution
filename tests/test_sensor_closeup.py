import base64
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest

spec = importlib.util.spec_from_file_location(
    'sensor_request', Path(__file__).parents[1] / 'scripts/prepare_sensor_target_request.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_closeup_preserves_sensor_pixels_and_original_mapping(tmp_path):
    Image.new('RGB', (640, 360), (12, 34, 56)).save(tmp_path / 'right.png')
    content = module.closeup_content(tmp_path, 'right', [180, 120, 410, 240])
    assert 'ORIGINAL full-frame pixel_uv' in content[0]['text']
    assert '"original_box_xyxy": [180, 120, 410, 240]' in content[0]['text']
    encoded = content[1]['image_url']['url'].split(',', 1)[1]
    with Image.open(io.BytesIO(base64.b64decode(encoded))) as crop:
        assert crop.size == (640, 334)
        assert crop.getpixel((0, 0)) == (12, 34, 56)


@pytest.mark.parametrize('box', [[-1, 0, 10, 10], [0, 0, 641, 10], [10, 0, 10, 10]])
def test_closeup_rejects_invalid_bounds(tmp_path, box):
    Image.new('RGB', (640, 360)).save(tmp_path / 'right.png')
    with pytest.raises(ValueError, match='crop bounds'):
        module.closeup_content(tmp_path, 'right', box)


def test_high_resolution_overview_and_crop_use_original_coordinates(tmp_path):
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080), (12, 34, 56)).save(tmp_path / f'{role}.png')
    assert module.capture_dimensions(tmp_path) == (1920, 1080)
    overview = module.overview_content(tmp_path, 'right')
    assert 'Original sensor size 1920x1080' in overview[0]['text']
    assert 'displayed overview 640x360' in overview[0]['text']
    assert 'Original u = displayed u * 3.0' in overview[0]['text']
    crop = module.closeup_content(tmp_path, 'right', [540, 360, 1230, 720])
    assert '"original_box_xyxy": [540, 360, 1230, 720]' in crop[0]['text']


def test_mismatched_sensor_dimensions_rejected(tmp_path):
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (640, 360) if role != 'right' else (1920, 1080)).save(
            tmp_path / f'{role}.png')
    with pytest.raises(ValueError, match='matching camera'):
        module.capture_dimensions(tmp_path)


def test_high_resolution_correspondence_prompt_and_bounded_inputs(tmp_path):
    for role in ('left', 'right', 'wrist'):
        Image.new('RGB', (1920, 1080)).save(tmp_path / f'{role}.png')
    (tmp_path / 'state.json').write_text(json.dumps({'observation_id': 'test:0'}))
    output = tmp_path / 'messages.json'
    subprocess.run([sys.executable, str(Path(module.__file__)), '--capture', str(tmp_path),
                    '--stage', 'correspondence', '--closeup-right', '540', '360', '1230',
                    '720', '--output', str(output)], check=True)
    content = json.loads(output.read_text())[0]['content']
    assert '1920x1080 integer pixels' in content[0]['text']
    for part in content:
        if part['type'] == 'image_url':
            encoded = part['image_url']['url'].split(',', 1)[1]
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as shown:
                assert max(shown.size) <= 640
