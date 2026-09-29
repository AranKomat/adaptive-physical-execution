#!/usr/bin/env python3
"""One bounded exploratory simulator grasp/lift from an inspected pregrasp."""
import argparse
import json
import os
from pathlib import Path
import time
from uuid import uuid4
import numpy as np
from physical_exec.contracts import ActionChunk
from physical_exec.transport import LocalClient, decode_observation, decode_result
from physical_exec.trace import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected-observation", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    client = LocalClient("http://127.0.0.1:8765", os.environ["PHYSICAL_EXEC_SIM_TOKEN"])
    started = time.monotonic(); count = 0
    summary = dict(task_success_claimed=False, grasp_verified=False, error=None,
                   gpt_calls=0, condition="operator-designed simulator-only grasp probe; grasp assist may be ON")
    try:
        obs = decode_observation(client.call("/observe"))
        if obs.key != args.expected_observation: raise ValueError("unexpected live observation")
        initial = obs.eef_pose.copy()
        phases = [("descend", initial[:3]+[0,0,-.035], 1., 30),
                  ("close", initial[:3]+[0,0,-.035], 0., 12),
                  ("lift", initial[:3]+[0,0,.025], 0., 40)]
        write_json(args.output/"plan.json", {"initial_id":obs.key,
                   "phases":[dict(name=n,hand_xyz=t.tolist(),open_fraction=g,max_actions=m) for n,t,g,m in phases],
                   "limits":"unchanged; no automatic retry; unknown contact/clearance"})
        with (args.output/"events.jsonl").open("w") as log:
            for name,target,grip,budget in phases:
                for i in range(budget):
                    if time.monotonic()-started > 120: raise RuntimeError("wall budget")
                    delta = target-obs.eef_pose[:3]; distance = np.linalg.norm(delta)
                    if name != "close" and distance <= .003: break
                    pose = obs.eef_pose.copy()
                    pose[:3] += delta*min(1.,.007/max(distance,1e-9))
                    action = ActionChunk("eef_absolute_world", np.array([np.r_[pose,grip]]),
                                         obs.key,obs.control_dt,"grasp_lift_probe")
                    reply = client.call("/step",dict(command_id=uuid4().hex,action=action.to_dict()),mutating=True)
                    log.write(json.dumps(dict(phase=name,action=action.to_dict(),result=reply))+"\n"); log.flush()
                    step = decode_result(reply); obs = step.observation; count += step.receipt.executed_steps
                    if step.receipt.status != "executed": raise RuntimeError("non-executed receipt")
                if name != "close" and np.linalg.norm(target-obs.eef_pose[:3]) > .003:
                    raise RuntimeError(name+" failed arrival; no next phase")
                summary[name+"_final_open_fraction"] = obs.gripper_open
                summary[name+"_observation_id"] = obs.key
        summary["sequence_completed"] = True
    except Exception as exc:
        summary["error"] = str(exc)
    finally:
        client.close(); summary.update(executed_actions=count,wall_seconds=time.monotonic()-started)
        write_json(args.output/"result.json",summary); print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
