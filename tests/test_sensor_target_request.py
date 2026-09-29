import json
from pathlib import Path
import subprocess
import sys

import pytest


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
