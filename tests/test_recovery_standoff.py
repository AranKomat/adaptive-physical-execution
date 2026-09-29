from dataclasses import replace
import json
from types import SimpleNamespace

import numpy as np
import pytest

from physical_exec.errors import InputRejected
from test_correction_checkpoint import load_script


@pytest.mark.parametrize('case', ['dry', 'execute', 'stop', 'stale', 'bounds'])
def test_recovery_standoff_contract(monkeypatch, tmp_path, observation, case):
    module = load_script('run_reviewed_recovery_standoff')
    initial = replace(observation, eef_pose=np.array([.4, 0, .3, 1, 0, 0, 0]),
                      gripper_open=1., control_dt=1/15)
    calls = []

    class Client:
        current = initial

        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def call(self, route, envelope=None, **kwargs):
            if route == '/metadata':
                return dict(real_hardware_supported=False, local_stages_enabled=True,
                            continuous_transit_enabled=True, contact_tracking_guard_enabled=True,
                            last_gripper_command=1.)
            if route == '/observe':
                return self.current
            assert route == '/local-stage'
            action = envelope['action']
            assert action['gripper_open'] == 1. and action['contact_tracking_guard']
            assert action['hand_pose_world'][2] >= .2
            calls.append(action)
            self.current = replace(self.current, seq=self.current.seq+64,
                                   eef_pose=np.asarray(action['hand_pose_world']))
            reason = ('contact tracking guard stopped motion' if case == 'stop' else
                      'local stage arrived' if action['settle_at_end'] else 'transit waypoint passed')
            receipt = SimpleNamespace(reason=reason, to_dict=lambda: dict(reason=reason))
            return SimpleNamespace(receipt=receipt, observation=self.current)

    fake_kin = SimpleNamespace(fk=lambda joints: initial.eef_pose,
        solve=lambda pose, seed, base, **kwargs: SimpleNamespace(converged=True, joints=seed))
    monkeypatch.setattr(module.URDFKinematics, 'from_urdf', lambda path: fake_kin)
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda value: value)
    monkeypatch.setattr(module, 'decode_result', lambda value: value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN', 'test-only')
    key = 'other:0' if case == 'stale' else initial.key
    audit, review = tmp_path/'audit.json', tmp_path/'review.json'
    audit.write_text(json.dumps(dict(observation_id=key, candidates=[dict(
        hand_pose_world=[.45, .02, .01 if case == 'bounds' else .14, 1, 0, 0, 0])])))
    review.write_text(json.dumps(dict(observation_id=key, decision='approve_standoff',
                                     contact_authorized=False, candidate_index=0)))
    monkeypatch.setattr(module.sys, 'argv', ['test', '--url', 'http://unused',
        '--audit', str(audit), '--review', str(review), '--output', str(tmp_path/'out')]
        + ([] if case == 'dry' else ['--execute']))
    if case in ('stale', 'bounds'):
        with pytest.raises((ValueError, InputRejected)):
            module.main()
        assert not calls
    elif case == 'stop':
        with pytest.raises(RuntimeError, match='no retry'):
            module.main()
        assert len(calls) == 1
        assert json.loads((tmp_path/'out'/'result.json').read_text())['status'] == 'stopped_without_retry'
    else:
        module.main()
        assert bool(calls) == (case == 'execute')
        if calls:
            assert any(not action['settle_at_end'] for action in calls)
            assert calls[-1]['hand_pose_world'][2] == pytest.approx(.2)
