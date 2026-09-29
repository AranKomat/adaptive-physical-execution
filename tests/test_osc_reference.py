import numpy as np
import pytest
from physical_exec.osc_reference import (ReferenceOSC, validate_plan, ramped_target, motion_stop_reason,
                                         NativeDiffIKFeedback, phases_at_cadence)


def test_opt_in_rotation_integral_stays_bounded():
    from physical_exec.geometry import rotvec_to_quat
    current = [0,0,.3,1,0,0,0]
    target = np.r_[0,0,.3,rotvec_to_quat([0,0,.04])]
    enabled = NativeDiffIKFeedback(.02,.097,control_dt=1/15,rotation_integral_feedback=True)
    default = NativeDiffIKFeedback(.02,.097,control_dt=1/15)
    for _ in range(100):
        action = enabled.command(current,target,.012)
        assert np.linalg.norm(action[3:6]*.097) <= .05+1e-12
    assert enabled.rotation_integral[2] == pytest.approx(.03)
    assert default.command(current,target,.012)[5]*.097 == pytest.approx(.04)
    assert np.all(default.rotation_integral == 0)


def test_reference_units_and_integral():
    controller = ReferenceOSC()
    current = [0, 0, .3, 1, 0, 0, 0]
    target = [.01, 0, .3, 1, 0, 0, 0]
    first = controller.command(current, target, .012)
    assert first[0] == pytest.approx(.5175)
    assert first[-2:].tolist() == [.012, .012]
    assert controller.command(current, target, .012)[0] == pytest.approx(.535)


def test_clamps_match_reference():
    controller = ReferenceOSC()
    a = controller.command([0, 0, .3, 1, 0, 0, 0], [1, 0, .3, 0, 1, 0, 0], .04)
    assert a[0] == 5 and a[3] == 5
    assert np.isfinite(a).all()


def plan():
    return dict(observation_id="episode:0", finish=True, phases=[dict(
        name="approach", hand_pose_world=[.3, -.3, .4, 0, 0, 1, 0],
        finger_position_m=.04, actions=180)])


def test_plan_guards():
    assert len(validate_plan(plan(), "episode:0", 180)) == 1
    with pytest.raises(ValueError):
        validate_plan(plan(), "episode:1", 180)
    with pytest.raises(ValueError):
        validate_plan(plan(), "episode:0", 179)
    p = plan()
    p["phases"][0]["finger_position_m"] = 1
    with pytest.raises(ValueError):
        validate_plan(p, "episode:0", 180)


def test_ramp_and_stops():
    a = [0,0,.3,1,0,0,0]
    b = [.03,0,.3,1,0,0,0]
    assert ramped_target(a,b,1)[0] == pytest.approx(.0015)
    np.testing.assert_allclose(ramped_target(a,b,30),b)
    with pytest.raises(ValueError):
        ramped_target(a,[0,0,.3,0,1,0,0],1)
    limits = np.tile([-2.,2.],(7,1))
    assert motion_stop_reason(a,b,np.zeros(7),limits) is None
    assert 'orientation' in motion_stop_reason(a,[0,0,.3,0,1,0,0],np.zeros(7),limits)
    assert 'joint limit' in motion_stop_reason(a,b,np.full(7,1.999),limits)


def test_native_feedback_and_cadence():
    c = NativeDiffIKFeedback(.02,.097)
    a = c.command([0,0,.3,1,0,0,0],[.3,0,.3,1,0,0,0],.012)
    np.testing.assert_allclose(a,[.5,0,0,0,0,0,.012,.012])
    assert phases_at_cadence(plan(),1/48)[0]['actions'] == 576
    assert phases_at_cadence(plan(),1/15)[0]['actions'] == 180
    assert validate_plan(dict(observation_id='a',phases=[],finish=True),'a',0) == []
    with pytest.raises(ValueError):
        validate_plan(dict(observation_id='a',phases=[],finish=False),'a',10)


def test_native_integral_feedback_is_bounded_and_time_scaled():
    c = NativeDiffIKFeedback(.02,.097,control_dt=.02,integral_feedback=True)
    a = c.command([0,0,.3,1,0,0,0],[.01,0,.3,1,0,0,0],.012)
    assert a[0] == pytest.approx((.01+.525*.02*.01)/.02)
    for _ in range(1000):
        a = c.command([0,0,.3,1,0,0,0],[1,0,.3,1,0,0,0],.012)
    assert a[0] == pytest.approx(1.5)
    assert c.position_integral[0] == pytest.approx(.03)
