import numpy as np
import pytest
from physical_exec.backends.flux import gripper_boundary_conversion
from physical_exec.errors import InputRejected


def test_opt_in_only_changes_small_gripper_overshoot():
    raw = np.zeros((1, 3, 8))
    raw[0, :, :7] = np.arange(7)
    raw[0, :, -1] = [-.00446, .3, 1.009]
    saved = raw.copy()
    with pytest.raises(InputRejected):
        gripper_boundary_conversion(raw, 0)
    out, audit = gripper_boundary_conversion(raw, .01)
    np.testing.assert_array_equal(raw, saved)
    np.testing.assert_array_equal(out[:, :7], raw[0, :, :7])
    np.testing.assert_allclose(out[:, -1], [0, .3, 1])
    assert audit['changed_indices'] == [0, 2]
    assert audit['raw_closed_fractions'] == raw[0, :, -1].tolist()
    assert audit['joint_targets_modified'] is False


@pytest.mark.parametrize('value', [-.010001, 1.010001, np.nan, np.inf])
def test_large_or_nonfinite_predictions_rejected(value):
    raw = np.zeros((2, 8)); raw[:, -1] = value
    with pytest.raises(InputRejected):
        gripper_boundary_conversion(raw, .01)


@pytest.mark.parametrize('tolerance', [-1, .02, np.nan])
def test_invalid_tolerance_rejected(tolerance):
    with pytest.raises(InputRejected):
        gripper_boundary_conversion(np.zeros((2, 8)), tolerance)
