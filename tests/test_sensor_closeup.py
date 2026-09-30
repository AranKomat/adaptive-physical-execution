import base64
import importlib.util
import io
from pathlib import Path

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
