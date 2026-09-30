import importlib.util
import json
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).resolve().parents[1]/'scripts/prepare_sensor_target_request.py'
    spec = importlib.util.spec_from_file_location('target_request_aperture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('mismatch', [False, True])
def test_experience_is_labeled_allowlisted_and_provenance_checked(tmp_path, mismatch):
    for condition, aperture in [('03', .3), ('00', 0.)]:
        obs = f'episode{condition}:575'
        (tmp_path/f'condition{condition}_review.json').write_text(json.dumps(dict(
            observation_id=obs, aperture_command=aperture,
            visual_retention=condition == '03', hidden='DO_NOT_INCLUDE')))
        run = tmp_path/f'gpu_aperture_pair{condition}_lift'
        run.mkdir()
        (run/'03_observation.json').write_text(json.dumps(dict(observation_id=obs, hidden='DO_NOT_INCLUDE')))
        (run/'03_receipt.json').write_text(json.dumps(dict(resulting_observation_id='wrong' if mismatch else obs)))
        (run/'03_left.png').write_bytes(b'fixture')
    module = load_script()
    if mismatch:
        with pytest.raises(ValueError, match='provenance'):
            module.aperture_experience_content(tmp_path)
    else:
        content = module.aperture_experience_content(tmp_path)
        text = json.dumps(content)
        assert 'DO_NOT_INCLUDE' not in text
        assert 'not current grasp verification' in text
        assert 'gripper_open' in text and 'force command' in text
        assert sum(x['type'] == 'image_url' for x in content) == 2
