import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'


def test_ram_prompt_is_explicit_and_does_not_reuse_gpu_target(tmp_path):
    (tmp_path/'state.json').write_text(json.dumps({'observation_id': 'ram:0'}))
    for role in ('left', 'right', 'wrist'):
        (tmp_path/f'{role}.png').write_bytes(b'test-image')
    output = tmp_path/'messages.json'
    subprocess.run([sys.executable, str(SCRIPT), '--capture', str(tmp_path),
                    '--output', str(output), '--stage', 'approach',
                    '--target-object', 'ram_module'], check=True)
    content = json.loads(output.read_text())[0]['content']
    prompt = content[0]['text']
    assert 'RAM module' in prompt and 'graphics card' not in prompt
    assert 'axis_samples' in prompt and 'NOT authorization' in prompt
    assert len([p for p in content if p['type'] == 'image_url']) == 3


def test_ram_rejects_gpu_only_stage_before_reading_capture(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), '--capture', str(tmp_path),
                            '--output', str(tmp_path/'out'), '--stage', 'carry',
                            '--target-object', 'ram_module'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'GPU-specific' in result.stderr
    assert not (tmp_path/'out').exists()
