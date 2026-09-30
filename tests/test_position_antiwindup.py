import numpy as np

from physical_exec.osc_reference import NativeDiffIKFeedback


def controller():
    return NativeDiffIKFeedback(.02, .1, control_dt=1/15, integral_feedback=True)


def test_downward_ramp_integral_cannot_drive_past_crossed_target():
    feedback = controller()
    feedback.position_integral[:] = [0., 0., -.0064]
    measured = [0., 0., .1645, 1., 0., 0., 0.]
    target = [0., 0., .1669, 1., 0., 0., 0.]
    action = feedback.command(measured, target, .04)
    assert action[2] > 0
    assert 0 < feedback.position_integral[2] < .0001


def test_reset_is_per_axis_and_preserves_same_direction_load_compensation():
    feedback = controller()
    feedback.position_integral[:] = [.004, -.005, -.006]
    feedback.command([0., 0., 0., 1., 0., 0., 0.],
                     [.002, -.002, .002, 1., 0., 0., 0.], .04)
    np.testing.assert_allclose(feedback.position_integral, [.00407, -.00507, .00007])


def test_submillimeter_crossing_does_not_clear_load_compensation():
    feedback = controller()
    feedback.position_integral[2] = -.006
    feedback.command([0., 0., 0., 1., 0., 0., 0.],
                     [0., 0., .0005, 1., 0., 0., 0.], .04)
    assert feedback.position_integral[2] < -.0059
