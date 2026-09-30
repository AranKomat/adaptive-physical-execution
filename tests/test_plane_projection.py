import copy

import numpy as np
import pytest

from physical_exec.depth import project_pixel_to_surface_plane


def inputs():
    camera = dict(observation_id='e:1', intrinsic_matrix=[[100,0,3],[0,100,3],[0,0,1]],
                  camera_position_world=[1,2,3], camera_quaternion_world_wxyz_optical=[1,0,0,0])
    plane = dict(observation_id='e:1', plane_rms_m=0., plane_sample_count=9,
                 plane_normal_world_up_hemisphere=[0,0,1], surface_point_world_m=[1,2,5],
                 pixel_uv=[3,3])
    return camera, [4,3], (7,7), plane


def test_plane_intersection_is_explicitly_inferred_not_sampled():
    result = project_pixel_to_surface_plane(*inputs())
    np.testing.assert_allclose(result['inferred_point_world_m'], [1.02,2,5])
    assert result['inferred'] is True
    assert 'surface_point_world_m' not in result
    assert 'NOT measured opening depth' in result['limitation']


@pytest.mark.parametrize('fault', ['stale','parallel','behind','noisy','nan','outside'])
def test_plane_projection_rejects_bad_geometry(fault):
    camera, pixel, shape, plane = copy.deepcopy(inputs())
    if fault == 'stale': plane['observation_id'] = 'e:0'
    if fault == 'parallel': plane['plane_normal_world_up_hemisphere'] = [0,1,0]
    if fault == 'behind': plane['surface_point_world_m'][2] = 2.
    if fault == 'noisy': plane['plane_rms_m'] = .01
    if fault == 'nan': plane['plane_rms_m'] = float('nan')
    if fault == 'outside': pixel[0] = 8
    with pytest.raises(ValueError):
        project_pixel_to_surface_plane(camera, pixel, shape, plane)
