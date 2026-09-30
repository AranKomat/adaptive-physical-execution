import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def fixture(tmp_path, selection_id='e:10', calibration_id='e:10'):
    (tmp_path/'state.json').write_text(json.dumps({
        'observation_id': 'e:10', 'hand_pose_world': [0, 0, 0, 1, 0, 0, 0]}))
    for camera in ('left', 'right', 'wrist'):
        Image.new('RGB', (20, 20)).save(tmp_path/f'{camera}.png')
        np.save(tmp_path/f'{camera}_depth.npy', np.full((20, 20), .5))
        (tmp_path/f'{camera}_calibration.json').write_text(json.dumps({
            'observation_id': calibration_id, 'depth_units': 'meters',
            'depth_convention': 'camera_optical_z',
            'intrinsic_matrix': [[100, 0, 10], [0, 100, 10], [0, 0, 1]],
            'camera_position_world': [0, 0, 0],
            'camera_quaternion_world_wxyz_optical': [1, 0, 0, 0]}))
    selection = tmp_path/'selection.json'
    selection.write_text(json.dumps({'observation_id': selection_id, 'samples': [{
        'camera': 'right', 'pixel_uv': [10, 10],
        'surface_hypothesis': 'operator hypothesis, not semantic truth'}]}))
    (tmp_path/'hidden_evaluator.json').write_text('{"oracle":"DO_NOT_INCLUDE"}')
    return selection


def run(tmp_path, selection, opening='.3'):
    return subprocess.run([sys.executable, str(Path(__file__).parents[1]/
        'scripts/prepare_grasp_contact_proposal.py'), '--capture', str(tmp_path),
        '--selection', str(selection), '--opening', opening, '--output', str(tmp_path/'output')],
        capture_output=True, text=True, check=False)


def test_proposal_is_bounded_observation_only_and_keeps_raw_measurements(tmp_path):
    selection = fixture(tmp_path)
    result = run(tmp_path, selection)
    assert result.returncode == 0, result.stderr
    proposal = json.loads((tmp_path/'output/proposal.json').read_text())
    assert proposal['max_steps'] == 64
    assert proposal['contact_tracking_guard'] is True
    assert proposal['lift_authorized'] is False
    assert proposal['automatic_retry'] is False
    measurements = json.loads((tmp_path/'output/measurements.json').read_text())
    assert measurements['samples'][0]['status'] == 'measured'
    assert measurements['samples'][0]['measurement']['surface_point_world_m'] == [0, 0, .5]
    messages = (tmp_path/'output/messages.json').read_text()
    assert 'DO_NOT_INCLUDE' not in messages
    assert 'unknown' in messages and 'NOT strict' in messages


@pytest.mark.parametrize('selection_id,calibration_id', [('e:9', 'e:10'), ('e:10', 'e:9')])
def test_rejects_stale_sensor_inputs_before_writing(tmp_path, selection_id, calibration_id):
    selection = fixture(tmp_path, selection_id, calibration_id)
    assert run(tmp_path, selection).returncode != 0
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('opening', ['nan', '-.1', '1.0'])
def test_rejects_unbounded_or_nonclosure_setpoint(tmp_path, opening):
    selection = fixture(tmp_path)
    assert run(tmp_path, selection, opening).returncode != 0
    assert not (tmp_path/'output').exists()


def test_invalid_depth_does_not_become_clearance_evidence(tmp_path):
    selection = fixture(tmp_path)
    np.save(tmp_path/'right_depth.npy', np.full((20, 20), np.nan))
    result = run(tmp_path, selection)
    assert result.returncode == 0, result.stderr
    row = json.loads((tmp_path/'output/measurements.json').read_text())['samples'][0]
    assert row['status'] == 'rejected'
    assert 'measurement' not in row
