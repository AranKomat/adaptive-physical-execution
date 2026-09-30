import json
import runpy
from pathlib import Path

import pytest
from PIL import Image

build = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                          'scripts/prepare_manipulation_review.py'))['build_messages']


@pytest.mark.parametrize('old_id,measurement_id,accepted', [
    ('e:1', 'e:1', True), ('other:1', 'other:1', False),
    ('e:2', 'e:2', False), ('e:1', 'e:0', False)])
def test_review_preserves_historical_provenance(tmp_path, old_id, measurement_id, accepted):
    current, old = tmp_path/'current', tmp_path/'old'
    for directory, observation_id in ((current, 'e:2'), (old, old_id)):
        directory.mkdir()
        (directory/'state.json').write_text(json.dumps({'observation_id': observation_id}))
        for role in ('left', 'right', 'wrist'):
            Image.new('RGB', (640, 360)).save(directory/f'{role}.png')
        (directory/'evaluator.json').write_text('HIDDEN_SENTINEL')
    args = (current, old, {'observation_id': measurement_id},
            {'observation_id': old_id}, 'Assisted carry; no contact attempt.')
    if not accepted:
        with pytest.raises(ValueError):
            build(*args)
        return
    result = build(*args)
    text = json.dumps(result)
    assert 'HISTORICAL measured samples' in text
    assert 'OPERATOR episode note (not sensor evidence)' in text
    assert 'no command is automatically executed' in text
    assert 'HIDDEN_SENTINEL' not in text
    assert sum(x['type'] == 'image_url' for x in result[0]['content']) == 4


def test_native_manipulation_review_uses_current_pixel_coordinates_and_crop(tmp_path):
    current, old = tmp_path/'current', tmp_path/'old'
    for directory, key in ((current, 'e:2'), (old, 'e:1')):
        directory.mkdir()
        (directory/'state.json').write_text(json.dumps({'observation_id': key}))
        for role in ('left', 'right', 'wrist'):
            Image.new('RGB', (1920, 1080)).save(directory/f'{role}.png')
    result = build(current, old, {'observation_id': 'e:1'}, {'observation_id': 'e:1'},
                   'Guard stopped contact; no release or retry.', [970, 390, 1290, 570])
    content = result[0]['content']
    assert '1920x1080 integer pixel_uv' in content[0]['text']
    assert '640x360 integer pixel_uv' not in content[0]['text']
    assert sum(p['type'] == 'image_url' for p in content) == 5
    assert any('970 + displayed_u' in p.get('text', '') for p in content)
