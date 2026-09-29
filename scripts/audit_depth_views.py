#!/usr/bin/env python3
"""Cross-view depth agreement; occluded points are not calibration failures."""
import argparse
import json
from pathlib import Path
import numpy as np
from physical_exec.geometry import quat_to_matrix


def compare(root, source, target, stride=8, tolerance=.01):
    def load(role):
        base = root / (role + "_depth") / "000000"
        c = json.loads(base.with_suffix(".json").read_text())
        return (np.load(base.with_suffix(".npy")), c,
                np.array(c["intrinsic_matrix"]),
                quat_to_matrix(c["camera_quaternion_world_wxyz_optical"]),
                np.array(c["camera_position_world"]))
    ds, cs, ks, rs, ps = load(source)
    dt, ct, kt, rt, pt = load(target)
    if cs["observation_id"] != ct["observation_id"]:
        raise ValueError("cross-view observations differ")
    v, u = np.mgrid[0:ds.shape[0]:stride, 0:ds.shape[1]:stride]
    z = ds[v, u].ravel()
    good = np.isfinite(z) & (z > 0)
    pixels = np.stack([u.ravel(), v.ravel(), np.ones(z.size)])[:, good]
    world = rs @ (np.linalg.solve(ks, pixels) * z[good]) + ps[:, None]
    camera = rt.T @ (world - pt[:, None])
    projected = kt @ camera
    positive = camera[2] > 0
    projected = projected[:, positive]; camera = camera[:, positive]
    uv = np.rint(projected[:2] / projected[2]).astype(int)
    inside = ((uv[0] >= 0) & (uv[0] < dt.shape[1]) &
              (uv[1] >= 0) & (uv[1] < dt.shape[0]))
    uv = uv[:, inside]; expected = camera[2, inside]
    measured = dt[uv[1], uv[0]]
    valid = np.isfinite(measured) & (measured > 0)
    residual = measured[valid] - expected[valid]
    return dict(source=source, target=target, compared=len(residual),
                agrees_within_1cm=int(np.sum(np.abs(residual) <= tolerance)),
                occluded_or_mismatch=int(np.sum(residual < -tolerance)),
                in_front_of_measured_surface=int(np.sum(residual > tolerance)),
                note="Nearest-pixel comparison; edges, occlusion and render artifacts remain confounders.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    args = parser.parse_args()
    roles = ["left", "right", "wrist"]
    print(json.dumps([compare(args.recording, a, b) for a in roles for b in roles if a != b], indent=2))


if __name__ == "__main__":
    main()
