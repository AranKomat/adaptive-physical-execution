#!/usr/bin/env python3
"""Compile operator-marked legal RAM surfaces into a nonclosing review proposal."""
import argparse
import base64
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.depth import surface_point
from physical_exec.geometry import matrix_pose, pose_error


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--center', nargs=2, required=True, type=int)
    p.add_argument('--axis-a', nargs=2, required=True, type=int)
    p.add_argument('--axis-b', nargs=2, required=True, type=int)
    p.add_argument('--camera', choices=['left','right','wrist'], default='wrist')
    p.add_argument('--holder-pixel', nargs=2, type=int, action='append', default=[],
                   help='Operator-marked visible support sample in the selected current camera')
    p.add_argument('--selection-history', type=Path,
                   help='Earlier same-episode model selection, explicitly refreshed with current depth')
    args = p.parse_args()
    state = json.loads((args.capture/'state.json').read_text())
    history = None
    if args.selection_history:
        history = json.loads(args.selection_history.read_text())
        episode, step = state['observation_id'].rsplit(':',1)
        old_episode, old_step = history['observation_id'].rsplit(':',1)
        expected = [{'camera':args.camera,'pixel_uv':pixel} for pixel in (args.axis_a,args.axis_b)]
        if (episode != old_episode or int(old_step) >= int(step)
                or history.get('decision') != 'target' or history.get('camera') != args.camera
                or history.get('pixel_uv') != args.center or history.get('axis_samples') != expected):
            raise ValueError('Historical selection must match pixels/camera in an earlier same-episode observation')
    c = json.loads((args.capture/f'{args.camera}_calibration.json').read_text())
    if c['observation_id'] != state['observation_id']:
        raise ValueError('Detached calibration')
    d = np.load(args.capture/f'{args.camera}_depth.npy', allow_pickle=False)
    measurements = [surface_point(d, c, pixel, radius=1, max_spread_m=.01)
                    for pixel in (args.center, args.axis_a, args.axis_b)]
    points = np.array([m['surface_point_world_m'] for m in measurements])
    axis = points[2]-points[1]
    if not .02 <= np.linalg.norm(axis) <= .2 or abs(axis[2]) > .003:
        raise ValueError('Insufficient or nonhorizontal measured axis')
    axis[2] = 0
    axis /= np.linalg.norm(axis)
    poses = []
    for sign in (-1, 1):
        x = sign*axis
        z = np.array([0., 0., -1.])
        t = np.eye(4)
        t[:3,:3] = np.column_stack((x, np.cross(z, x), z))
        t[:3,3] = points[0]+[0, 0, .1034-.005]
        poses.append(matrix_pose(t))
    pose = min(poses, key=lambda q: np.linalg.norm(pose_error(state['hand_pose_world'], q)[3:]))
    plan = dict(observation_id=state['observation_id'], measured_surface=measurements[0],
        heading_world_quaternion=pose[3:].tolist(), bite_depth_m=.005,
        target_hand_pose_world=pose.tolist(), axis_measurements=measurements[1:],
        target_source='Operator-marked current RGB-D top strip and long axis; not autonomous targeting',
        contact_authorized=False, limitation='Nominal robot pinch offset and5mm bite assumption; '
        'not opposing-contact, support-clearance or swept-volume certification.')
    plan['camera'] = args.camera
    plan['holder_measurements'] = [surface_point(d, c, pixel, radius=1, max_spread_m=.01)
                                   for pixel in args.holder_pixel]
    plan['holder_measurement_limit'] = ('Operator-marked visible surfaces only; not maximum holder '
        'height, hidden geometry, minimum clearance, or collision certification.')
    if history is not None:
        plan['target_source'] = 'Historical model pixels on CURRENT legal depth; static scene/feature identity assumption; not a fresh selection'
        plan['historical_selection'] = history
    prompt = ('Review this simulator-only RAM PRE-CLOSURE proposal using current images and legal '
        'depth measurements. Module is upright in a holder; hand is open at a standoff. '
        'Read target_source and any historical_selection below for how these pixels were selected. '
        'Historical pixel reuse assumes the camera and feature correspondence remained valid; '
        'reject visible contradiction or occlusion rather than trusting depth continuity alone. '
        'These are surface measurements, NOT privileged object poses. '
        'Proposal: rotate open hand at its CURRENT elevated position so hand x follows module long '
        'axis (jaws close perpendicular), then descend to nominal pinch center5mm below selected top. '
        'No closure, lift or insertion. Nominal hand-to-pinch103.4mm; nominal finger end112.9mm. '
        'Use only any current holder_measurements supplied below, with their limitations. '
        'Absent samples, holder height is unknown. Minimum clearance remains unestablished. '
        'Do not import holder measurements from earlier modules or episodes. '
        'Assess whether the fingers appear able to straddle this module '
        'without entering its support; do not confuse light strip with load-bearing evidence. '
        'Unknown clearance stays exploratory. Tracking guards stop on10mm/.10rad ramp error, '
        'but are not collision certification. Up to16*64 actions,15Hz, continuous segments, '
        'settle after rotation and final arrival. Stop/no retry on nonarrival or guard. '
        'Return JSON: observation_id, decision (approve_preclosure/inspect/stop), '
        'contact_authorized:false, evidence, uncertainty. Approval is only for open-hand placement, '
        'not grasp success. If approach looks obstructed or wrong, reject it.\n'
        +json.dumps(plan)+'\nCurrent robot state: '+json.dumps(state))
    content = [{'type':'text', 'text':prompt}]
    for role in ('left','right','wrist'):
        content.extend([{'type':'text','text':'CURRENT '+role}, {'type':'image_url','image_url':{
            'url':'data:image/png;base64,'+base64.b64encode((args.capture/f'{role}.png').read_bytes()).decode()}}])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'plan.json').write_text(json.dumps(plan,indent=2))
    (args.output/'messages.json').write_text(json.dumps([{'role':'user','content':content}]))
    print(json.dumps(plan,indent=2))


if __name__ == '__main__':
    main()
