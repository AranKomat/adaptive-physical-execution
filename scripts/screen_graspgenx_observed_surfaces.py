#!/usr/bin/env python3
"""Screen nominal gripper proxies against observed surfaces, never certify clearance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.geometry import quat_to_matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--proposals', type=Path, required=True)
    parser.add_argument('--mesh', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.mesh.read_bytes()).hexdigest() != '6feba508f92c6c6609d6639c4c2883200aaacd31f507370d479b25be1ea0e3b8':
        raise ValueError('Expected pinned nominal canonical Panda collision proxy')
    state = json.loads((args.capture/'state.json').read_text())
    points, labels, pixels = [], [], []
    for role in ('left', 'right', 'wrist'):
        calibration = json.loads((args.capture/f'{role}_calibration.json').read_text())
        if calibration['observation_id'] != state['observation_id']:
            raise ValueError('Detached calibration')
        if calibration['depth_convention'] != 'camera_optical_z' or calibration['depth_units'] != 'meters':
            raise ValueError('Unsupported depth')
        depth = np.load(args.capture/f'{role}_depth.npy', allow_pickle=False)
        v, u = np.mgrid[0:depth.shape[0]:2, 0:depth.shape[1]:2]
        z = depth[v, u]
        rays = np.stack([u, v, np.ones_like(u)], -1) @ np.linalg.inv(calibration['intrinsic_matrix']).T
        world = (rays*z[..., None]) @ quat_to_matrix(calibration['camera_quaternion_world_wxyz_optical']).T
        world += calibration['camera_position_world']
        keep = (np.isfinite(world).all(axis=-1) & (z > 0)
                & (world >= [-.2, -1, -.05]).all(axis=-1)
                & (world <= [1, 1, .8]).all(axis=-1))
        points.append(world[keep]); pixels.append(np.stack([u, v], -1)[keep])
        labels.extend([role]*int(keep.sum()))
    points, pixels, labels = np.concatenate(points), np.concatenate(pixels), np.asarray(labels)
    mesh = trimesh.load(args.mesh, force='mesh')
    parts = mesh.split(only_watertight=False)
    if not all(part.is_watertight for part in parts):
        raise ValueError('Expected watertight component proxies')
    poses = np.load(args.proposals, allow_pickle=False)['world_from_canonical']
    rows = []
    for index, pose in enumerate(poses):
        for phase, height in [('contact_hypothesis', 0.), ('raised_standoff', .06)]:
            transform = pose.copy(); transform[2, 3] += height
            local = (points-transform[:3, 3]) @ transform[:3, :3]
            penetration = np.zeros(len(points))
            # Union component interiors; parity over overlapping components can cancel.
            for part in parts:
                selected = np.flatnonzero(((local >= part.bounds[0]) & (local <= part.bounds[1])).all(axis=1))
                if not len(selected):
                    continue
                selected = selected[part.contains(local[selected])]
                if len(selected):
                    distance = trimesh.proximity.signed_distance(part, local[selected])
                    penetration[selected] = np.maximum(penetration[selected], distance)
            hits = penetration > .002
            examples = []
            for role in ('left', 'right', 'wrist'):
                indices = np.flatnonzero(hits & (labels == role))
                if len(indices):
                    i = indices[np.argmax(penetration[indices])]
                    examples.append(dict(camera=role, pixel_uv=pixels[i].tolist(),
                        surface_world_m=points[i].tolist(), proxy_penetration_m=float(penetration[i]),
                        count=int(len(indices))))
            vertices = mesh.vertices @ transform[:3, :3].T + transform[:3, 3]
            rows.append(dict(candidate=index, phase=phase, observed_points_inside_proxy_over_2mm=int(hits.sum()),
                             nominal_gripper_min_world_z_m=float(vertices[:, 2].min()), examples=examples))
    result = dict(observation_id=state['observation_id'], observed_points=len(points),
        mesh_components=len(parts), rows=rows, motion_authorized=False,
        limitations=['Nominal public gripper proxy, not verified native collider geometry.',
            'Observed surface points can include the current robot, intended object, or background. Inspect named pixels before attributing conflict.',
            'No hits is not free-space or swept-volume certification; occluded space is unknown.',
            'Endpoint tests only; no arm geometry or approach trajectory checked.'])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    for row in rows:
        print(row['candidate'], row['phase'], row['observed_points_inside_proxy_over_2mm'], row['examples'], flush=True)


if __name__ == '__main__':
    main()
