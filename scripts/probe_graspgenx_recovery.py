#!/usr/bin/env python3
"""One pinned GraspGen-X proposal batch; no simulator client or robot actions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET

import numpy as np

SOURCE_REVISION = 'b9429097728cb1c430dd78b92edf17ba318aad03'
WEIGHT_HASHES = {
    'gen/config.yaml': '16aedbdc23441a1db818261b865f55bd71451d6224fc514615e0d1ab744b7dcb',
    'dis/config.yaml': '43cf8ea0ade67d938040bde0df318b3f4c9c19e4f88d97052dc175df2c28c8e7',
    'gen/epoch_736.pth': '8b55f31cdb8340a573b4df27b027c15cff326bd6debcb389bf631d2aaab7ac44',
    'dis/epoch_1056.pth': 'cbf3f3bdb2e4c03fca8486ed24de0e6a8a859e6bd22bce2f1434a610335abd3e',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def panda_hand_transform(path):
    joint = ET.parse(path).getroot().find("joint[@name='world_joint']")
    if (joint is None or joint.get('type') != 'fixed'
            or joint.find('parent').get('link') != 'world'
            or joint.find('child').get('link') != 'panda_hand'):
        raise ValueError('Unexpected canonical-to-hand joint')
    origin = joint.find('origin')
    xyz = np.asarray([float(v) for v in origin.get('xyz').split()])
    rpy = np.asarray([float(v) for v in origin.get('rpy').split()])
    if (xyz.shape != (3,) or rpy.shape != (3,) or not np.isfinite(rpy).all()
            or not np.array_equal(xyz, np.zeros(3)) or not np.array_equal(rpy[:2], np.zeros(2))):
        raise ValueError('Expected zero-translation yaw-only Panda frame')
    yaw = rpy[2]
    transform = np.eye(4)
    transform[:3, :3] = [[np.cos(yaw), -np.sin(yaw), 0],
                        [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]
    return transform


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(300)
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = dict(complete=False, inference_attempts=0, robot_actions=0, paid_calls=0)
    try:
        source = Path('/workspace/graspgenx-source')
        weights = Path('/workspace/graspgenx-weights/release')
        assets = Path('/workspace/graspgenx-assets/franka_panda')
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != SOURCE_REVISION:
            raise ValueError('Source revision mismatch')
        subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD', '--', 'graspgenx'], check=True)
        for name, expected in WEIGHT_HASHES.items():
            if digest(weights/name) != expected:
                raise ValueError('Weight/config checksum mismatch: '+name)
        if digest(assets/'config.json') != 'a1fe1b7c9d77bbd568e4f656fab65e2da083d4c387f239150e89a6c6451961de':
            raise ValueError('Panda conditioning config mismatch')
        if digest(assets/'gripper.urdf') != 'b49f211b29b61e6bedef627a3ec6bc7c11026099ae2db30cc51fc2d60ff3d93c':
            raise ValueError('Panda frame URDF mismatch')
        manifest = json.loads((args.input/'manifest.json').read_text())
        if manifest['coordinate_frame'] != 'world' or digest(args.input/'points_world.npy') != manifest['cloud_sha256']:
            raise ValueError('Detached cloud/frame')
        points = np.load(args.input/'points_world.npy', allow_pickle=False)
        if points.shape != (4096, 3) or not np.isfinite(points).all():
            raise ValueError('Invalid cloud')
        receipt.update(source_revision=revision, input_manifest=manifest,
                       gripper_asset_revision='19a03c00d19aeaf052d0f6801f0041982d676e8a')
        os.environ['GRASPGENX_CHECKPOINT_DIR'] = str(weights.parent)
        os.environ['GRASPGENX_GRIPPER_CFG_DIR'] = str(assets.parent)
        import torch
        torch.set_num_threads(2)
        torch.cuda.set_per_process_memory_fraction(.45)
        random.seed(0)
        np.random.seed(0)
        torch.manual_seed(0)
        from graspgenx.grasp_server import GraspGenXSampler
        from graspgenx.utils.checkpoint_io import load_model_cfg
        from graspgenx.x_grippers import make_sweep_volume_gripper_info
        cfg = load_model_cfg(weights/'gen', weights/'dis', 'epoch_736.pth', 'epoch_1056.pth')
        if any(x.gripper_backbone != 'sweep_volume_v2' for x in (cfg.diffusion, cfg.discriminator)):
            raise ValueError('Asset-free conditioning requires sweep_volume_v2')
        hand = json.loads((assets/'config.json').read_text())
        sv = hand['sweep_volume']
        info = make_sweep_volume_gripper_info(sv['extents'], sv['offset'], sv['extents2'],
            sv['offset2'], gripper_type=0, fingertip_depth=hand['fingertip'][2], name='franka_panda')
        sampler = GraspGenXSampler(cfg, gripper_info=info, use_tensorrt=False)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        receipt['inference_attempts'] = 1
        start = time.monotonic()
        poses, scores = GraspGenXSampler.run_inference(points, sampler, grasp_threshold=-1.,
            num_grasps=32, topk_num_grasps=8, min_grasps=1, max_tries=1, remove_outliers=False)
        torch.cuda.synchronize()
        receipt['inference_seconds'] = time.monotonic()-start
        poses, scores = poses.detach().cpu().numpy(), scores.detach().cpu().numpy()
        if poses.size and (poses.shape != (len(scores), 4, 4) or not np.isfinite(poses).all()
                           or not np.isfinite(scores).all()):
            raise ValueError('Malformed proposals')
        # Dataset root -> actual panda_hand is an explicit fixed URDF transform.
        transform = panda_hand_transform(assets/'gripper.urdf')
        if not poses.size:
            poses = np.empty((0, 4, 4))
        hand_poses = poses @ transform if poses.size else np.empty((0, 4, 4))
        np.savez_compressed(args.output/'proposals.npz', world_from_canonical=poses,
                           world_from_panda_hand=hand_poses, scores=scores)
        receipt.update(complete=True, proposals=len(scores), canonical_from_hand=transform.tolist(),
            peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,
            peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,
            conditioning=sv, seed=0, collision_checked=False, motion_authorized=False,
            limitation='Partial historical planar cloud; scores are not contact/clearance certification.')
    except Exception:
        receipt['error'] = traceback.format_exc()
        raise
    finally:
        (args.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps({k: v for k, v in receipt.items() if k != 'input_manifest'}), flush=True)


if __name__ == '__main__':
    main()
