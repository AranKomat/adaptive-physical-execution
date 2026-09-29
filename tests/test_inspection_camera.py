import numpy as np
import pytest
from physical_exec.inspection_camera import camera_path

HAND = [.3,-.3,.45,0,0,1,0]

def test_bounded_continuous_camera_path():
    path = camera_path([.45,.5,1.4],[.85,.3,1.05],HAND,HAND,288,1/48)
    np.testing.assert_allclose(path[-1],[.85,.3,1.05])
    assert np.max(np.linalg.norm(np.diff(path,axis=0),axis=1))*48 <= .12

@pytest.mark.parametrize('eye,hand,actions', [
    ([.85,.3,.7], HAND, 288),
    ([.85,.3,1.05], [.4,-.3,.45,0,0,1,0], 288),
    ([.85,.3,1.05], HAND, 10),
    ([float('nan'),.3,1.05], HAND, 288),
])
def test_reject_unbounded_camera_commands(eye,hand,actions):
    with pytest.raises(ValueError):
        camera_path([.45,.5,1.4],eye,HAND,hand,actions,1/48)


def test_oblique_envelope_requires_explicit_opt_in():
    start, end = [.55,-.65,.4], [.6,-.35,.7]
    with pytest.raises(ValueError):
        camera_path(start,end,HAND,HAND,64,1/15)
    path = camera_path(start,end,HAND,HAND,64,1/15,oblique_envelope=True)
    np.testing.assert_allclose(path[-1],end)
    assert np.max(np.linalg.norm(np.diff(path,axis=0),axis=1))*15 <= .12
    with pytest.raises(ValueError):
        camera_path(start,[.6,0.,1.1],HAND,HAND,64,1/15,oblique_envelope=True)


@pytest.mark.parametrize('camera_writes_work',[True,False])
def test_integrated_camera_hold_and_failed_readback(monkeypatch,observation,camera_writes_work):
    from dataclasses import replace
    from types import SimpleNamespace, ModuleType
    import sys
    from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment
    from physical_exec.errors import AmbiguousExecution

    fake_torch = ModuleType('torch')
    fake_torch.float32 = np.float32
    fake_torch.as_tensor = lambda value,**kwargs: np.asarray(value)
    monkeypatch.setitem(sys.modules,'torch',fake_torch)
    module = ModuleType('robobench.controllers.diff_ik')
    module.DiffIKControllerCfg = lambda **kwargs: SimpleNamespace(pos_scale=.05,rot_scale=.2)
    module.DiffIKController = lambda cfg: SimpleNamespace(bind=lambda robot:None,
                                                         compute=lambda value:np.zeros((1,7)))
    monkeypatch.setitem(sys.modules,'robobench.controllers.diff_ik',module)
    camera = SimpleNamespace(_view=SimpleNamespace(_use_fabric=True),
                             data=SimpleNamespace(pos_w=np.array([[.55,-.65,.4]])))
    camera_calls = []
    def set_camera(eye,gaze):
        camera_calls.append(np.asarray(eye).copy())
        if camera_writes_work:
            camera.data.pos_w = np.asarray(eye).copy()
    camera.set_world_poses_from_view = set_camera
    env = EmbodiedSWEEnvironment.__new__(EmbodiedSWEEnvironment)
    env.current = observation
    env.allow_local_stages = env.allow_inspection_camera = True
    env.local_stage_rotation_integral = False
    env._last_gripper_command = 1.
    env._poisoned = False
    env._evaluation = SimpleNamespace(success=False)
    env.record_episode = None
    env.joint_names = observation.joint_names
    env.kin = SimpleNamespace(limits=np.tile([-3.,3.],(7,1)))
    env.camera_map = {'right':'external_right'}
    env.task_config = {'extra_cameras':{'external_right':{'target':[.22,-.34,.2]}}}
    env.sim = SimpleNamespace(sensors={'external_right':camera},
                              env=SimpleNamespace(robot=object(),device='cpu'))
    actions = []
    def step(action,cid):
        actions.append(action)
        env.current = replace(env.current,seq=env.current.seq+1)
    env.step = step
    value = dict(observation_id=observation.key,hand_pose_world=observation.eef_pose.tolist(),
                 gripper_open=1.,max_steps=64,target_source='TEST CAMERA HOLD',
                 camera_eye_world=[.6,-.35,.7])
    if camera_writes_work:
        result = env.local_stage(value,'test')
        assert result.receipt.executed_steps == 64
        assert result.receipt.reason == 'local stage arrived'
        assert not env._poisoned
    else:
        with pytest.raises(AmbiguousExecution,match='never retry'):
            env.local_stage(value,'test')
        assert env._poisoned
    assert len(actions) == len(camera_calls) == 64
    assert all(action.values[0][-1] == 1. for action in actions)
