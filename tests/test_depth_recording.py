import json
from types import SimpleNamespace
import numpy as np
import pytest
from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment


def test_depth_recording_preserves_invalid_and_excludes_object_state(tmp_path):
    env = object.__new__(EmbodiedSWEEnvironment)
    env.camera_map = {"left": "camera"}
    env.record_episode = tmp_path
    data = SimpleNamespace(
        output={"distance_to_image_plane": np.array([[[[1.], [np.inf]], [[0.], [2.]]]])},
        intrinsic_matrices=np.eye(3)[None], pos_w=np.zeros((1, 3)),
        quat_w_ros=np.array([[1., 0., 0., 0.]]), object_pose="must not leak",
    )
    env.sim = SimpleNamespace(sensors={"camera": SimpleNamespace(data=data)})
    env.seq = 0
    obs = SimpleNamespace(key="episode:0", images={"left": np.zeros((2, 2, 3), dtype=np.uint8)})
    env._record_depth(obs)
    depth = np.load(tmp_path / "left_depth/000000.npy", allow_pickle=False)
    assert np.isinf(depth[0, 1]) and depth[1, 0] == 0
    meta = json.loads((tmp_path / "left_depth/000000.json").read_text())
    assert meta["depth_convention"] == "camera_optical_z"
    assert meta["policy_input"] is False
    assert "object_pose" not in meta
    obs.images["left"] = np.zeros((3, 3, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="alignment"):
        env._record_depth(obs)
