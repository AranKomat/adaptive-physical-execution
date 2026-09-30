import copy

import pytest

from physical_exec.carry import carry_stages, lift_endpoint_completed, validate_lift_diagnostic


def receipt():
    return dict(status='executed', reason='local stage budget ended without arrival',
                requested_steps=64, executed_steps=64,
                tracking_position_error_m=.004573, tracking_rotation_error_rad=.000102)


def test_accepts_bounded_endpoint_without_modifying_receipt():
    value = receipt()
    original = copy.deepcopy(value)
    assert lift_endpoint_completed(value)
    assert value == original


@pytest.mark.parametrize('field,value', [
    ('reason', 'contact tracking guard stopped'), ('reason', 'transit waypoint passed'),
    ('status', 'aborted'), ('executed_steps', 63), ('requested_steps', 65),
    ('tracking_position_error_m', .01001), ('tracking_position_error_m', float('nan')),
    ('tracking_position_error_m', True), ('tracking_position_error_m', -.001),
    ('tracking_rotation_error_rad', .03001), ('tracking_rotation_error_rad', None),
])
def test_rejects_guard_stops_and_out_of_bounds(field, value):
    item = receipt()
    item[field] = value
    assert not lift_endpoint_completed(item)


def stages():
    hand = [.3, -.3, .23, 0, 0, 1, 0]
    plan = dict(observation_id='episode:1', finish=False, target_source='test', phases=[
        dict(name='elevated_carry_lift_diagnostic', finger_position_m=.012,
             hand_pose_world=[.3, -.3, .46, 0, 0, 1, 0])])
    result = carry_stages(plan, 'episode:1', hand, .3)
    for stage in result:
        stage['contact_tracking_guard'] = True
    return hand, result


def test_allows_only_bounded_upward_schedule():
    hand, sequence = stages()
    validate_lift_diagnostic(sequence, hand)


@pytest.mark.parametrize('change', ['lateral', 'descend', 'far', 'rotation', 'guard', 'settle', 'budget'])
def test_rejects_other_motion(change):
    hand, sequence = stages()
    stage = sequence[-1]
    if change == 'lateral': stage['hand_pose_world'][0] += .002
    if change == 'descend': stage['hand_pose_world'][2] = .2
    if change == 'far': stage['hand_pose_world'][2] = .5
    if change == 'rotation': stage['hand_pose_world'][3:] = [1, 0, 0, 0]
    if change == 'guard': stage['contact_tracking_guard'] = False
    if change == 'settle': stage['settle_at_end'] = False
    if change == 'budget': stage['max_steps'] = 65
    with pytest.raises(ValueError):
        validate_lift_diagnostic(sequence, hand)
