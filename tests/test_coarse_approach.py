import copy

import pytest

from physical_exec.carry import coarse_approach_stage


def inputs():
    def sample(point):
        return {'measurement': dict(observation_id='e:1', surface_point_world_m=point,
                                    local_depth_spread_m=.001, neighborhood_radius_pixels=1)}
    measurements = dict(observation_id='e:1',
                        connector={'samples': [sample([.4,0,.17]), sample([.45,0,.17])]},
                        socket={'samples': [sample([.4,.01,.03]), sample([.45,.01,.03])]})
    review = dict(observation_id='e:1', decision='approve_coarse_approach', descent_m=.04)
    return measurements, review, 'e:1', [.42,0,.37,1,0,0,0], .3


def test_coarse_approach_preserves_grip_and_only_descends_four_cm():
    stage = coarse_approach_stage(*inputs())
    assert stage['hand_pose_world'] == [.42,0,.33,1,0,0,0]
    assert stage['gripper_open'] == .3
    assert stage['contact_tracking_guard'] is True
    assert stage['max_steps'] == 64
    assert 'NOT insertion' in stage['target_source']


@pytest.mark.parametrize('fault', ['stale', 'denied', 'wrong_distance', 'nested_stale',
                                 'single_pixel', 'too_close', 'short_axis', 'transverse', 'nan'])
def test_coarse_approach_rejects_unsupported_geometry_or_review(fault):
    m, r, key, hand, opening = copy.deepcopy(inputs())
    if fault == 'stale': m['observation_id'] = 'e:0'
    if fault == 'denied': r['decision'] = 'inspect'
    if fault == 'wrong_distance': r['descent_m'] = .05
    sample = m['connector']['samples'][0]['measurement']
    if fault == 'nested_stale': sample['observation_id'] = 'e:0'
    if fault == 'single_pixel': sample['neighborhood_radius_pixels'] = 0
    if fault == 'too_close': sample['surface_point_world_m'][2] = .10
    if fault == 'short_axis': sample['surface_point_world_m'][0] = .449
    if fault == 'transverse':
        for s in m['socket']['samples']: s['measurement']['surface_point_world_m'][1] = .08
    if fault == 'nan': sample['local_depth_spread_m'] = float('nan')
    with pytest.raises(ValueError):
        coarse_approach_stage(m, r, key, hand, opening)
