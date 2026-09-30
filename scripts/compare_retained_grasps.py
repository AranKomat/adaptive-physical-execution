"""Read-only comparison of retained grasp commands; never generates motion."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sources = {}

    def read(path):
        raw = path.read_bytes()
        sources[str(path.relative_to(args.runs))] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    reference = args.runs/'guarded_full_lift_20261001_execution'
    close = json.loads(read(reference/'10_request.json'))['action']
    close_receipt = json.loads(read(reference/'10_receipt.json'))
    lift = json.loads(read(reference/'14_request.json'))['action']
    lift_receipt = json.loads(read(reference/'14_receipt.json'))
    records = []
    for name in ('gpu_depth_direct_a_continue7_20260930',
                 'gpu_depth_direct_a_regrasp_guard9_20260930',
                 'gpu_depth_direct_a_fresh_grasp12_continue13_20260930'):
        events = [json.loads(line) for line in read(args.runs/name/'events.jsonl').splitlines()]
        request = next(e['data']['request'] for e in events
                       if e['kind'] == 'local_stage_requested'
                       and e['data']['request']['gripper_open'] == 0)
        receipts = [e['data'] for e in events if e['kind'] == 'execution_receipt']
        records.append(dict(run=name, closure_request=request,
            closure_xyz_minus_reference_mm=(1000*(
                np.array(request['hand_pose_world'][:3])
                - np.array(close['hand_pose_world'][:3]))).tolist(),
            receipts=receipts))
    result = dict(scope='read-only cross-run command comparison; not causal ablation',
        limitations=['Different episodes, selected surfaces, controller revisions and lift schedules.',
                     'Commanded opening is not measured contact, force, or achieved width.',
                     'Reference targets must not be reused as current object state.',
                     'Native grasp assistance is a confound, not evidence of unassisted capture.'],
        reference=dict(closure_request=close, closure_receipt=close_receipt,
                       final_lift_request=lift, final_lift_receipt=lift_receipt),
        comparisons=records, source_sha256=sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps([dict(run=r['run'], delta_mm=r['closure_xyz_minus_reference_mm'])
                      for r in records], indent=2))


if __name__ == '__main__':
    main()
