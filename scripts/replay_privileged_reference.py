#!/usr/bin/env python3
"""Replay an unchanged external solution as a PRIVILEGED current-substrate baseline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--solution', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-actions', type=int, default=5000)
    parser.add_argument('--seed', type=int, default=0)
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path[:0] = [str(args.solution.resolve()), str(args.repo.resolve())]
    manifest = {str(p.relative_to(args.solution)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(args.solution.rglob('*.py'))}
    (args.output / 'source_hashes.json').write_text(json.dumps(manifest, indent=2))
    app = AppLauncher(args).app
    result = dict(condition='privileged frozen solution on current pc_gpu OSC substrate',
                  nonprivileged_success=False, seed=args.seed, actions=0, stages=[])
    started = time.monotonic()
    try:
        import robobench
        robobench.discover()
        from robobench.core import ENVS
        from stages import stage_1, stage_2, stage_3
        from solve import solve
        env = ENVS.get('assembly.pc_gpu.franka.osc')().build(
            num_envs=1, device='cuda:0', seed=args.seed)
        env.reset(seed=args.seed)
        original_step = env.step
        with (args.output / 'trajectory.jsonl').open('w') as stream:
            def step(action, *a, **kw):
                if result['actions'] >= args.max_actions:
                    raise RuntimeError('Action cap reached; no automatic retry')
                original_step(action, *a, **kw)
                result['actions'] += 1
                if result['actions'] % 10 == 0:
                    row = dict(action=result['actions'],
                               card_position=env.scene.card.data.root_pos_w.tolist(),
                               card_quaternion=env.scene.card.data.root_quat_w.tolist(),
                               held=env.scene.grasp_held.tolist(),
                               seated=env.scene.seated().tolist())
                    stream.write(json.dumps(row) + '\n')
                    stream.flush()
            env.step = step
            for module in (stage_1, stage_2, stage_3):
                original_check = module.check
                def check(e, original=original_check, name=module.__name__):
                    passed = bool(original(e))
                    row = dict(stage=name, passed=passed, actions=result['actions'])
                    result['stages'].append(row)
                    print(json.dumps(row), flush=True)
                    return passed
                module.check = check
            solve(env)
            result.update(success=bool(env.scene.success().all()),
                          seated=bool(env.scene.seated().all()),
                          grasp_held=bool(env.scene.grasp_held.any()))
    except Exception:
        result['error'] = traceback.format_exc()
        traceback.print_exc()
    result['wall_seconds'] = time.monotonic() - started
    (args.output / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
    # Isaac shutdown may hang; evidence is flushed before terminating this owned process.
    os._exit(2 if 'error' in result else 0)


if __name__ == '__main__':
    main()
