import json
from pathlib import Path
import runpy

import pytest


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
            (directory/f'{role}.png').write_bytes(b'fixture')
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
