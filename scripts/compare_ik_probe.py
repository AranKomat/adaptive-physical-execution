#!/usr/bin/env python3
"""Fresh-episode controller comparison; no object-state input or task-success claim."""
import argparse
import os
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["native", "integrated"], required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repo", required=True)
    if os.environ.get("OMNI_KIT_ACCEPT_EULA", "").upper() != "YES":
        raise SystemExit("Existing Isaac license acceptance required")
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args(); args.enable_cameras = True
    args.output.mkdir(parents=True, exist_ok=False)
    app = AppLauncher(args).app
    import numpy as np
    import torch
    from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment
    from physical_exec.config import load_task
    from physical_exec.contracts import ActionChunk
    from physical_exec.geometry import pose_error
    from physical_exec.trace import write_json
    task, limits = load_task("configs/tasks/pc_gpu.json")
    env = EmbodiedSWEEnvironment(args.repo, task, limits, record_dir=args.output/"recordings")
    obs = env.reset(0); target = obs.eef_pose.copy(); target[:3] += [.06, 0, -.06]
    write_json(args.output/"initial.json",obs.public_state())
    native = None
    if args.mode == "native":
        from robobench.controllers import DiffIKController, DiffIKControllerCfg
        native = DiffIKController(DiffIKControllerCfg(dt=.02, ee_body="panda_hand",
                                  arm_joint_names=env.sim.env.robot.ARM_JOINTS))
        native.bind(env.sim.env.robot)
    rows = []; error = None; started = time.monotonic()
    try:
        for i in range(60):
            e = pose_error(obs.eef_pose, target)
            waypoint = obs.eef_pose.copy()
            waypoint[:3] += e[:3]*min(1., .01/max(np.linalg.norm(e[:3]),1e-9))
            waypoint[3:] = target[3:]
            if native is not None:
                delta = pose_error(obs.eef_pose, waypoint)
                u = np.r_[delta[:3]/native.cfg.pos_scale,delta[3:]/native.cfg.rot_scale]
                q = native.compute(torch.as_tensor(u[None],dtype=torch.float32,device=env.sim.env.device))
                action = ActionChunk("joint_absolute",np.array([np.r_[q.detach().cpu().numpy()[0],1.]]),
                                     obs.key,obs.control_dt,"native_diffik_probe",obs.joint_names)
            else:
                action = ActionChunk("eef_absolute_world",np.array([np.r_[waypoint,1.]]),
                                     obs.key,obs.control_dt,"integrated_ik_probe")
            step = env.step(action, str(i)); obs = step.observation
            row = dict(step=obs.seq,error_m=float(np.linalg.norm(target[:3]-obs.eef_pose[:3])),
                       receipt=step.receipt.to_dict(),joints=obs.joints.tolist())
            rows.append(row)
            if row["error_m"] <= .003: break
    except Exception as exc:
        error = str(exc)
    write_json(args.output/"result.json",dict(mode=args.mode,rows=rows,error=error,
        initial_target=target.tolist(),wall_seconds=time.monotonic()-started,
        condition="upstream DiffIK algorithm at matched 15Hz outer cadence, NOT native 50Hz mode reproduction",
        task_success_claimed=False))
    print("RESULT_SAVED",args.output,flush=True)
    # Isaac teardown can hang; all evidence has been flushed. This owns the process.
    os._exit(0 if error is None else 2)


if __name__ == "__main__": main()
