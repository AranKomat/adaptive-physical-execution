from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from test_correction_checkpoint import load_script


@pytest.mark.parametrize('failure', [None, 'old_worker', 'nonarrival'])
def test_ramp_return_is_bounded_and_stops(monkeypatch, tmp_path, observation, failure):
    module = load_script('probe_local_stage_service')
    initial = replace(observation, seq=0, gripper_open=1.,
                      eef_pose=np.array([.22, -.34, .55, 0., 0., 1., 0.]))
    calls = []

    class Client:
        current = initial
        def __init__(self, *args, **kwargs):
            pass
        def close(self):
            pass
        def call(self, path, envelope=None, **kwargs):
            if path == '/metadata':
                return dict(local_stages_enabled=True, real_hardware_supported=False,
                    contact_tracking_guard_enabled=True,
                    position_integral_antiwindup=None if failure == 'old_worker'
                    else 'opposing_axis_reset_above_1mm')
            if path == '/reset':
                assert failure != 'old_worker'
                return self.current
            assert path == '/local-stage'
            action = envelope['action']
            calls.append(action)
            self.current = replace(self.current, seq=self.current.seq+64,
                                   eef_pose=np.array(action['hand_pose_world']))
            reason = ('local stage arrived' if action['settle_at_end']
                      else 'transit waypoint passed')
            if failure == 'nonarrival':
                reason = 'local stage budget ended without arrival'
            return SimpleNamespace(observation=self.current,
                receipt=SimpleNamespace(reason=reason, to_dict=lambda: {'test_double': True}))

    from physical_exec.kinematics import URDFKinematics
    monkeypatch.setattr(URDFKinematics, 'from_urdf', lambda *a: SimpleNamespace(
        fk=lambda q: [0, 0, 0, 1, 0, 0, 0],
        solve=lambda *a, **kw: SimpleNamespace(converged=True, joints=initial.joints)))
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda v: v)
    monkeypatch.setattr(module, 'decode_result', lambda v: v)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN', 'test-only')
    monkeypatch.setattr(module.sys, 'argv', ['probe', '--url', 'http://unused',
        '--output', str(tmp_path/'output'), '--contact-tracking-guard', '--ramp-return-qualification'])
    if failure:
        with pytest.raises((RuntimeError, ValueError)):
            module.main()
        assert len(calls) == (0 if failure == 'old_worker' else 1)
    else:
        module.main()
        assert len(calls) == 4
        assert [v['settle_at_end'] for v in calls] == [False, True, False, True]
        np.testing.assert_allclose([v['hand_pose_world'][2] for v in calls], [.61, .67, .61, .55])
        assert all(v['gripper_open'] == 1 and v['contact_tracking_guard'] for v in calls)
        assert sum(v['max_steps'] for v in calls) == 256
