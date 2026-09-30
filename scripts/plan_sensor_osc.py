#!/usr/bin/env python3
"""Convert a visual target into an explicit, inspectable pilot plan; does not execute."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from physical_exec.depth import surface_point
from physical_exec.osc_reference import validate_plan
from physical_exec.trace import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--response', type=Path, required=True)
    parser.add_argument('--stage', choices=['approach', 'grasp'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse-pixel-template', action='store_true',
                        help='Explicit fixed-fixture replay of prior pixel choice on fresh depth; not a fresh model decision')
    parser.add_argument('--operator-selected', action='store_true',
                        help='Label a current operator pixel selection, not a model decision')
    parser.add_argument('--pause-after-grasp', action='store_true',help='leave the episode paused for visual review and a separate command')
    args = parser.parse_args()
    if args.operator_selected and args.reuse_pixel_template:
        raise ValueError('Operator selection and cached model replay are distinct conditions')
    response = json.loads(args.response.read_text())
    state = json.loads((args.capture/'state.json').read_text())
    if response['decision'] != 'target' or (not args.reuse_pixel_template and response['observation_id'] != state['observation_id']):
        raise ValueError('No fresh visual target')
    camera = response['camera']
    if camera not in ('left', 'right', 'wrist'):
        raise ValueError('Invalid camera')
    calibration = json.loads((args.capture/f'{camera}_calibration.json').read_text())
    if calibration['observation_id'] != state['observation_id']:
        raise ValueError('Stale calibration')
    depth = np.load(args.capture/f'{camera}_depth.npy', allow_pickle=False)
    pixel = np.asarray(response['pixel_uv'])
    if pixel.shape != (2,) or not np.isfinite(pixel).all() or not np.equal(pixel,np.floor(pixel)).all():
        raise ValueError('Pixel must contain two finite integers')
    # A narrow top surface may be under five pixels wide. Search at most two
    # pixels, with a 3x3 footprint and a tighter 10 mm discontinuity threshold.
    candidates = sorted([(dx,dy) for dx in range(-2,3) for dy in range(-2,3)
                         if dx*dx+dy*dy <= 4], key=lambda d:(d[0]**2+d[1]**2,d))
    point = None
    for delta in candidates:
        try:
            point = surface_point(depth, calibration, pixel+delta, radius=1, max_spread_m=.01)
            break
        except ValueError:
            continue
    if point is None:
        raise ValueError('No locally continuous depth patch near selected pixel; inspect again')
    surface = np.asarray(point['surface_point_world_m'])
    top_down = [0,0,1,0]
    def phase(name, xyz, finger, steps):
        return dict(name=name,hand_pose_world=[*xyz,*top_down],finger_position_m=finger,actions=steps)
    if args.stage == 'approach':
        phases = [phase('sensor_standoff',surface+[0,0,.22],.04,180)]
    else:
        # Known robot pinch-center offset, NOT object pose/geometry. The 15 mm
        # bite is an explicit generic pilot parameter, not a measured grasp.
        hand = surface + [0,0,.1034-.015]
        phases = [phase('sensor_descend',hand,.04,160),
                  phase('sensor_close',hand,.012,100),
                  phase('sensor_lift',hand+[0,0,.23],.012,180)]
    value = dict(observation_id=state['observation_id'], phases=phases,
                 reference_control_dt=1/15,finish=args.stage=='grasp' and not args.pause_after_grasp,
                 target_source=('cached Astra pixel template on fresh depth; fixed-fixture replay' if args.reuse_pixel_template
                                else 'current operator-selected image pixel plus legal measured depth; not autonomous targeting' if args.operator_selected
                                else 'fresh Astra image pixel plus legal measured depth; operator-defined phase sequence'),
                 selector_observation_id=response['observation_id'],
                 requested_pixel=pixel.tolist(), measured_surface=point, camera=camera,
                 limitations='Not a full object pose, certified clearance, or autonomous grasp planner. '
                 'At most 2px refinement; top-down attitude and bite depth are declared pilot assumptions.')
    validate_plan(value,state['observation_id'],700)
    write_json(args.output,value)
    print(json.dumps(value,indent=2))


if __name__ == '__main__':
    main()
