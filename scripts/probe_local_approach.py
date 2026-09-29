#!/usr/bin/env python3
"""Simulator-only sensor-grounded approach probe, not an autonomous grasp demo."""
import argparse
import json
import os
from pathlib import Path
import time
from uuid import uuid4
import numpy as np
from physical_exec.contracts import ActionChunk
from physical_exec.depth import surface_point
from physical_exec.transport import LocalClient, decode_observation, decode_result, encode_observation
from physical_exec.trace import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--depth", type=Path, required=True)
    p.add_argument("--pixel", nargs=2, type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--continue-run", type=Path, help="explicit bounded extension of a completed approach")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    calibration = json.loads(args.depth.with_suffix(".json").read_text())
    point = surface_point(np.load(args.depth, allow_pickle=False), calibration, args.pixel)
    target = np.array(point["surface_point_world_m"]) + [0, 0, .30]
    expected_id = calibration["observation_id"]
    if args.continue_run:
        previous = json.loads((args.continue_run / "result.json").read_text())
        plan = json.loads((args.continue_run / "plan.json").read_text())
        if previous["error"] is not None or previous["arrived"] or previous["executed_actions"] != 60:
            raise ValueError("only a completed, unambiguous 60-action approach can be extended")
        if not np.allclose(target, plan["target_hand_xyz"], atol=1e-10, rtol=0):
            raise ValueError("extension target differs")
        expected_id = previous["final_observation_id"]
    write_json(args.output / "plan.json", dict(measurement=point, target_hand_xyz=target.tolist(),
               standoff_world_z_m=.30, max_actions=60, max_seconds=120,
               gpt_calls=0, selection="operator-selected visual pixel", expected_observation_id=expected_id,
               continuation_of=str(args.continue_run) if args.continue_run else None,
               scope="SIMULATOR ONLY; unknown swept-volume clearance; approach not grasp"))
    if not args.execute:
        print("Plan saved; no commands issued."); return
    client = LocalClient("http://127.0.0.1:8765", os.environ["PHYSICAL_EXEC_SIM_TOKEN"])
    started = time.monotonic(); count = 0; best = float("inf"); stale = 0
    result = {"arrived": False, "error": None}
    try:
        obs = decode_observation(client.call("/observe"))
        if obs.key != expected_id:
            raise ValueError("depth observation must exactly match current episode/step")
        if np.linalg.norm(target-obs.eef_pose[:3]) > .30:
            raise ValueError("target exceeds bounded approach distance")
        with (args.output / "events.jsonl").open("w") as log:
            log.write(json.dumps({"initial_observation": encode_observation(obs)})+"\n")
            while count < 60 and time.monotonic()-started < 120:
                delta = target-obs.eef_pose[:3]; error = float(np.linalg.norm(delta))
                if error <= .003:
                    result["arrived"] = True; break
                if error < best-.0005: best = error; stale = 0
                else: stale += 1
                if stale >= 10:
                    result["stop_reason"] = "no measured progress"; break
                waypoint = obs.eef_pose.copy()
                waypoint[:3] += delta * min(1., .01/error)
                action = ActionChunk("eef_absolute_world", np.array([np.r_[waypoint, 1.]]),
                                     obs.key, obs.control_dt, "local_approach_probe")
                reply = client.call("/step", {"command_id": uuid4().hex, "action": action.to_dict()}, mutating=True)
                log.write(json.dumps({"action": action.to_dict(), "result": reply})+"\n"); log.flush()
                step = decode_result(reply); obs = step.observation; count += step.receipt.executed_steps
                if step.receipt.status != "executed":
                    result["stop_reason"] = "non-executed receipt"; break
            result["final_hand_error_m"] = float(np.linalg.norm(target-obs.eef_pose[:3]))
            result["final_observation_id"] = obs.key
            result.setdefault("stop_reason", "arrived" if result["arrived"] else
                              ("action_budget" if count >= 60 else "wall_budget"))
    except Exception as exc:
        result["error"] = str(exc)
        result["stop_reason"] = "rejected or ambiguous; no retry"
    finally:
        client.close()
        result.update(executed_actions=count, wall_seconds=time.monotonic()-started,
                      gpt_calls=0, task_success_claimed=False)
        write_json(args.output / "result.json", result)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
