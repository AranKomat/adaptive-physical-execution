#!/usr/bin/env python3
"""Compare a nominal robot closing line to legal depth; never certify a grasp or clearance."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import pose_matrix, quat_to_matrix


def classify(point, depth, calibration, tolerance=.005):
    if calibration['depth_convention'] != 'camera_optical_z' or calibration['depth_units'] != 'meters':
        raise ValueError('Requires metric optical-axis depth')
    optical = quat_to_matrix(calibration['camera_quaternion_world_wxyz_optical']).T @ (
        point-np.asarray(calibration['camera_position_world']))
    if optical[2] <= 0:
        return {'status':'behind_camera'}
    projected = np.asarray(calibration['intrinsic_matrix']) @ optical
    uv = projected[:2]/projected[2]
    u,v = np.rint(uv).astype(int)
    result = {'pixel_uv':uv.tolist(), 'point_optical_depth_m':float(optical[2])}
    if not 1 <= u < depth.shape[1]-1 or not 1 <= v < depth.shape[0]-1:
        return {**result,'status':'out_of_frame'}
    patch = depth[v-1:v+2,u-1:u+2]
    if not np.isfinite(patch).all() or np.any(patch <= 0):
        return {**result,'status':'invalid_depth'}
    spread = float(np.ptp(patch))
    result['depth_spread_m'] = spread
    if spread > .01:
        return {**result,'status':'depth_edge'}
    measured = float(np.median(patch))
    residual = float(optical[2]-measured)
    return {**result,'measured_optical_depth_m':measured,'behind_surface_m':residual,
            'status': 'occluded' if residual > tolerance else
                      'in_front_of_surface' if residual < -tolerance else 'surface_consistent'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation', type=Path, required=True)
    parser.add_argument('--recording', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    obs = json.loads(args.observation.read_text())
    if obs['robot'] != 'franka' or obs['eef_frame'] != 'panda_hand':
        raise ValueError('Only pinned Panda geometry supported')
    opening = obs['gripper_open_fraction']
    if not np.isfinite(opening) or not 0 <= opening <= 1:
        raise ValueError('Invalid measured aperture')
    transform = pose_matrix(obs['eef_pose_world_xyz_wxyz'])
    sensors = {}
    for role in ('left','right','wrist'):
        base = args.recording/f'{role}_depth'/f'{obs["step"]:06d}'
        calibration = json.loads(base.with_suffix('.json').read_text())
        if calibration['observation_id'] != obs['observation_id']:
            raise ValueError('Stale calibration')
        sensors[role] = (np.load(base.with_suffix('.npy'), allow_pickle=False), calibration)
    rows = []
    for y in np.linspace(-.04*opening,.04*opening,17):
        local = np.array([0,y,.1034,1.])
        world = (transform@local)[:3]
        rows.append({'hand_point_m':local[:3].tolist(), 'world_point_m':world.tolist(),
                     'views':{role:classify(world,*sensor) for role,sensor in sensors.items()}})
    value = {'observation_id':obs['observation_id'],'samples':rows,
             'limitation':'Nominal closing centerline only, not exact pad surfaces, finite finger volume, '
                          'object identity, contact force or grasp/clearance proof. Occluded samples are '
                          'unknown, not occupied/free. In-front samples concern only measured rays. '
                          '5mm comparison tolerance is diagnostic, not calibrated uncertainty.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({role:{status:sum(row['views'][role]['status']==status for row in rows)
                          for status in sorted({row['views'][role]['status'] for row in rows})}
                      for role in sensors},indent=2))


if __name__ == '__main__':
    main()
