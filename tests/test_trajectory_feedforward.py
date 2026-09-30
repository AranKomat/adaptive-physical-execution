import numpy as np
import pytest

from physical_exec.osc_reference import NativeDiffIKFeedback


def test_feedforward_at_zero_error_and_no_integral_windup():
    f = NativeDiffIKFeedback(.02,.097,control_dt=1/15,integral_feedback=True)
    pose = [0,0,.5,1,0,0,0]
    inc = [.005,0,0,0,0,.01]
    command = f.command(pose,pose,.04,trajectory_increment=inc)
    np.testing.assert_allclose(command[:6],np.array(inc)/[.02,.02,.02,.097,.097,.097])
    np.testing.assert_array_equal(f.position_integral,np.zeros(3))
    stopped = f.command(pose,pose,.04,trajectory_increment=np.zeros(6))
    np.testing.assert_array_equal(stopped[:6],np.zeros(6))


@pytest.mark.parametrize('increment', [[.016,0,0,0,0,0],[0,0,0,0,0,.041],
                                      [float('nan')]*6,[0]*5])
def test_invalid_feedforward_rejected(increment):
    f = NativeDiffIKFeedback(.02,.097,control_dt=1/15)
    with pytest.raises(ValueError):
        f.command([0,0,.5,1,0,0,0],[0,0,.5,1,0,0,0],.04,trajectory_increment=increment)


def test_combined_feedback_and_feedforward_still_capped():
    f = NativeDiffIKFeedback(.02,.097,control_dt=1/15,integral_feedback=True)
    command = f.command([0,0,.5,1,0,0,0],[.1,0,.5,1,0,0,0],.04,
                        trajectory_increment=[.01,0,0,0,0,0])
    assert np.linalg.norm(command[:3]*.02) <= .03+1e-12
