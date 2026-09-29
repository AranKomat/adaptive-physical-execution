#!/usr/bin/env python3
"""Proposal-only FLUX measurement from a retained capture; no simulator access."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import numpy as np
    from PIL import Image
    import torch
    from physical_exec.contracts import Observation
    from physical_exec.backends.flux import FluxEngine, droid_arrays, droid_output_to_chunk
    from physical_exec.trace import write_json

    data = json.loads((args.capture / "observation.json").read_text())
    index = json.loads((args.capture / "camera_index.json").read_text())
    images = {}
    for filename, role in index.items():
        with Image.open(args.capture / filename) as im:
            images[role] = np.asarray(im.convert("RGB"))
    obs = Observation(
        data["episode_id"], data["step"], data["sim_time_seconds"],
        data["task"], data["robot"], images, data["joints_rad"],
        tuple(data["joint_names"]), data["eef_pose_world_xyz_wxyz"],
        data["gripper_open_fraction"], data["control_dt_seconds"],
    )
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    engine = FluxEngine(args.checkpoint, {r: r for r in ("left", "right", "wrist")})
    torch.cuda.synchronize()
    load_seconds = time.monotonic() - started
    values = droid_arrays(obs, engine.camera_map)
    batch = {k: torch.from_numpy(v).to(engine.device) if isinstance(v, np.ndarray) else v
             for k, v in values.items()}
    started = time.monotonic()
    with torch.no_grad():
        raw = engine.policy.predict_action_chunk(batch)
    torch.cuda.synchronize()
    inference_seconds = time.monotonic() - started
    raw = raw.detach().float().cpu().numpy()
    np.save(args.output / "raw_proposal.npy", raw, allow_pickle=False)
    rejection = None
    try:
        action = droid_output_to_chunk(raw, obs, Path(engine.identity).name)
        write_json(args.output / "proposal.json", action.to_dict())
    except ValueError as error:
        rejection = str(error)
    metrics = {
        "load_seconds": load_seconds,
        "inference_seconds": inference_seconds,
        "proposal_rejection": rejection,
        "raw_shape": list(raw.shape),
        "raw_closed_fraction_range": [float(raw[..., -1].min()), float(raw[..., -1].max())],
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "robot_commands_executed": 0,
        "fk_and_execution_bounds_qualified": False,
    }
    write_json(args.output / "metrics.json", metrics)
    print(json.dumps(metrics), flush=True)


if __name__ == "__main__":
    main()
