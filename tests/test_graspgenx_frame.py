import numpy as np
import pytest

from test_correction_checkpoint import load_script


@pytest.mark.parametrize('xyz,child,valid', [
    ('0 0 0', 'panda_hand', True), ('0 0 .1', 'panda_hand', False),
    ('0 0 0', 'other_frame', False)])
def test_canonical_panda_frame(tmp_path, xyz, child, valid):
    module = load_script('probe_graspgenx_recovery')
    path = tmp_path/'gripper.urdf'
    path.write_text(f'''<robot><joint name="world_joint" type="fixed">
      <parent link="world"/><child link="{child}"/>
      <origin xyz="{xyz}" rpy="0 0 1.5708"/>
    </joint></robot>''')
    if not valid:
        with pytest.raises(ValueError):
            module.panda_hand_transform(path)
        return
    transform = module.panda_hand_transform(path)
    assert np.allclose(transform[:3, :3] @ [0, 1, 0], [-1, 0, 0], atol=1e-5)
    assert np.allclose(transform @ [0, 0, .1034, 1], [0, 0, .1034, 1])
    canonical = np.eye(4)
    canonical[:3, 3] = [.4, .1, .2]
    hand = canonical @ transform
    assert np.allclose(hand[:3, 3], canonical[:3, 3])
    assert not np.allclose(hand[:3, :3], canonical[:3, :3])
