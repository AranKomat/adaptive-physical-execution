import copy

import numpy as np
import pytest

from physical_exec.carry import carry_stages

HAND = [.3,-.3,.5,0,0,1,0]


def plan():
    return dict(observation_id='episode:5',finish=False,target_source='test sensor depth',
                phases=[dict(name='elevated_carry_1',finger_position_m=.012,
                             hand_pose_world=[.45,-.1,.5,0,0,1,0])])


def test_carry_preserves_height_grip_and_only_settles_at_end():
    stages = carry_stages(plan(),'episode:5',HAND,.3)
    assert len(stages) == 5
    assert [s['settle_at_end'] for s in stages] == [False]*4+[True]
    points = np.array([HAND[:3]]+[s['hand_pose_world'][:3] for s in stages])
    assert np.max(np.linalg.norm(np.diff(points,axis=0),axis=1)) <= .06
    assert all(s['gripper_open'] == .3 for s in stages)


@pytest.mark.parametrize('change', ['stale','descend','rotate','release','finish','far','wrong_phase'])
def test_reject_unsafe_carry_plan(change):
    value = copy.deepcopy(plan())
    phase = value['phases'][0]
    if change == 'stale': value['observation_id'] = 'episode:4'
    if change == 'descend': phase['hand_pose_world'][2] = .49
    if change == 'rotate': phase['hand_pose_world'][3:] = [1,0,0,0]
    if change == 'release': phase['finger_position_m'] = .04
    if change == 'finish': value['finish'] = True
    if change == 'far': phase['hand_pose_world'][0] = 1.
    if change == 'wrong_phase': phase['name'] = 'insert'
    with pytest.raises(ValueError):
        carry_stages(value,'episode:5',HAND,.3)
