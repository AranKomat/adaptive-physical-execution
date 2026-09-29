import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('mismatch', [None, 'episode', 'receipt'])
def test_review_provenance_and_no_evaluator_input(tmp_path, mismatch):
    before = dict(episode_id='episode', step=1, observation_id='episode:1')
    after = dict(episode_id='episode', step=2, observation_id='episode:2')
    receipt = dict(observation_id='episode:1', resulting_observation_id='episode:2')
    if mismatch == 'episode':
        after['episode_id'] = 'different'
    if mismatch == 'receipt':
        receipt['resulting_observation_id'] = 'episode:3'
    for name, value in [('before', before), ('after', after), ('receipt', receipt)]:
        (tmp_path/f'{name}.json').write_text(json.dumps(value))
    (tmp_path/'evaluator.json').write_text('EVALUATOR_SENTINEL')
    for prefix in ('before', 'after'):
        for role in ('left', 'right', 'wrist'):
            (tmp_path/f'{prefix}_{role}.png').write_bytes(b'image fixture')
    output = tmp_path/'messages.json'
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_continuation_review.py'
    result = subprocess.run([sys.executable, str(script), '--recovery', str(tmp_path),
                             '--output', str(output)], capture_output=True, text=True)
    if mismatch:
        assert result.returncode != 0
        assert not output.exists()
    else:
        assert result.returncode == 0, result.stderr
        messages = json.loads(output.read_text())
        content = messages[0]['content']
        assert sum(part['type'] == 'image_url' for part in content) == 6
        assert 'EVALUATOR_SENTINEL' not in output.read_text()
        assert 'under 450 words' in content[0]['text']
