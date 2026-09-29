#!/usr/bin/env python3
"""Feed a declared fixed-fixture sensor recipe, then pause after camera inspection.

No model calls, scene truth, automatic resets or retry after failed execution.
Run beside a separately launched pilot. This is experiment orchestration, not
an autonomous task planner. All motion targets are recomputed from fresh depth.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--approach-template', type=Path, required=True)
    p.add_argument('--grasp-template', type=Path, required=True)
    p.add_argument('--carry-template', type=Path, required=True)
    args = p.parse_args()
    scripts = Path(__file__).resolve().parent
    for required in (scripts/'plan_sensor_osc.py', scripts/'plan_sensor_carry.py',
                     args.approach_template, args.grasp_template, args.carry_template):
        if not required.is_file():
            raise FileNotFoundError(f'recipe dependency missing: {required}')
    episode = None
    for index in range(4):
        deadline = time.monotonic()+1800
        while True:
            if (args.run/'result.json').exists():
                raise RuntimeError('pilot ended; do not restart or replay commands')
            try:
                state = json.loads((args.run/'ready.json').read_text())
            except FileNotFoundError:
                state = None
            if state is not None and state['command_index'] == index:
                break
            if state is not None and state['command_index'] > index:
                raise RuntimeError('pilot advanced unexpectedly')
            if time.monotonic() > deadline:
                raise TimeoutError('observation wait expired; inspect existing worker, do not restart')
            time.sleep(1)
        current_episode, seq = state['observation_id'].split(':')
        if episode is not None and current_episode != episode:
            raise RuntimeError('episode changed')
        episode = current_episode
        if index and not state['last_stage']['arrival_passed']:
            raise RuntimeError('previous arrival failed; no continuation')
        capture = args.run/'captures'/f'{int(seq):06d}'
        target = args.run/f'command_{index}.json'
        temporary = args.run/f'planned_{index}.json'
        if target.exists():
            raise RuntimeError('command already exists; no duplicate dispatch')
        if index < 2:
            subprocess.run([sys.executable, str(scripts/'plan_sensor_osc.py'),
                '--capture', str(capture), '--response', str(args.approach_template if index == 0 else args.grasp_template),
                '--stage', 'approach' if index == 0 else 'grasp', '--reuse-pixel-template',
                '--pause-after-grasp', '--output', str(temporary)], check=True)
        elif index == 2:
            subprocess.run([sys.executable, str(scripts/'plan_sensor_carry.py'),
                '--capture', str(capture), '--response', str(args.carry_template),
                '--previous-command', str(args.run/'command_1.json'), '--reuse-pixel-template',
                '--output', str(temporary)], check=True)
        else:
            previous = json.loads((args.run/'command_2.json').read_text())
            phase = previous['phases'][-1]
            command = dict(observation_id=state['observation_id'], reference_control_dt=1/15,
                phases=[dict(name='post_carry_camera_inspection',
                             hand_pose_world=phase['hand_pose_world'], finger_position_m=.012,
                             actions=90, camera_eye_world=[.85,.3,1.05])], finish=False,
                target_source='operator-defined camera move; retain previous commanded hand target',
                limitations='Idealized camera without collision body; unknown clearance. No descent.')
            temporary.write_text(json.dumps(command)+'\n')
        temporary.rename(target)
        print(f'DISPATCHED {index} {state["observation_id"]}', flush=True)


if __name__ == '__main__':
    main()
