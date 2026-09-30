import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'plan_sensor_osc', Path(__file__).parents[1]/'scripts/plan_sensor_osc.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('width,radius', [(640, 2), (1280, 4), (1920, 6)])
def test_bounded_resize_search(width, radius):
    actual, offsets = module.refinement_offsets(width)
    assert actual == radius
    assert offsets[0] == (0, 0)
    assert all(x*x+y*y <= radius*radius for x, y in offsets)
    assert (0, -radius) in offsets


@pytest.mark.parametrize('width', [0, -1, 1921, 3840])
def test_unqualified_width_rejected(width):
    with pytest.raises(ValueError):
        module.refinement_offsets(width)
