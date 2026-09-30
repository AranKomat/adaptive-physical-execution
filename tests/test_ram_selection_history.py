"""Reject detached historical pixels before attempting depth or motion planning."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('change', [
    {'observation_id': 'other:0'},
    {'observation_id': 'episode:249'},
    {'observation_id': 'episode:250'},
    {'decision': 'inspect'},
    {'camera': 'wrist'},
    {'pixel_uv': [426, 146]},
    {'axis_samples': []},
])
def test_history_must_match_current_episode_and_selected_pixels(tmp_path, change):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'episode:249'}))
    history = dict(observation_id='episode:0', decision='target', camera='right',
                   pixel_uv=[425, 146], axis_samples=[
                       dict(camera='right', pixel_uv=[391, 132]),
                       dict(camera='right', pixel_uv=[462, 162])])
    history.update(change)
    path = tmp_path/'history.json'
    path.write_text(json.dumps(history))
    script = Path(__file__).resolve().parents[1]/'scripts/prepare_ram_preclosure.py'
    result = subprocess.run([sys.executable, str(script), '--capture', str(tmp_path),
        '--output', str(tmp_path/'output'), '--camera', 'right', '--center', '425', '146',
        '--axis-a', '391', '132', '--axis-b', '462', '162', '--selection-history', str(path)],
        capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Historical selection must match' in result.stderr
    assert not (tmp_path/'output').exists()
