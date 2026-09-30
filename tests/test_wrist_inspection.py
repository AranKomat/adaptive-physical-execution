import importlib.util
from pathlib import Path

import numpy as np
import pytest

from physical_exec.geometry import pose_error


def module():
    path = Path(__file__).resolve().parents[1]/'scripts/run_wrist_inspection.py'
    spec = importlib.util.spec_from_file_location('wrist_inspection', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_aim_preserves_position_and_caps_rotation():
    hand = [0, 0, .5, 1, 0, 0, 0]
    camera = dict(camera_position_world=[0, 0, .5], camera_quaternion_world_wxyz_optical=[0, 1, 0, 0])
    target = module().inspection_target(hand, camera, [.2, 0, .2])
    delta = pose_error(hand, target)
    np.testing.assert_allclose(delta[:3], 0)
    assert np.linalg.norm(delta[3:]) == pytest.approx(.2)


def test_rejects_low_hand():
    camera = dict(camera_position_world=[0, 0, .3], camera_quaternion_world_wxyz_optical=[0, 1, 0, 0])
    with pytest.raises(ValueError, match='elevated'):
        module().inspection_target([0, 0, .3, 1, 0, 0, 0], camera, [.1, 0, .1])
