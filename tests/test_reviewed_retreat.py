from dataclasses import replace
import json
from types import SimpleNamespace

import numpy as np
import pytest

from physical_exec.geometry import rotvec_to_quat
from test_correction_checkpoint import load_script


@pytest.mark.parametrize('case', ['complete', 'orientation', 'stall', 'eof', 'stale', 'oversize'])
def test_single_latch_retreat_stops(monkeypatch, tmp_path, observation, case):
    module = load_script('run_reviewed_retreat')
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
                return dict(real_hardware_supported=False, continuous_transit_enabled=True,
                            contact_tracking_guard_enabled=True, last_gripper_command=1.)
            if route == '/observe':
                return self.current
            assert route == '/local-stage'
            action = envelope['action']
            calls.append(action)
            assert action['max_steps'] == 1 and action['gripper_open'] == 1.
            assert action['settle_at_end'] is False and action['contact_tracking_guard']
            pose = np.asarray(action['hand_pose_world']).copy()
            if case == 'stall':
                pose = initial.eef_pose.copy()
            if case == 'orientation':
                pose[3:] = rotvec_to_quat([.03, 0, 0])
            self.current = replace(self.current, seq=self.current.seq+1, eef_pose=pose)
            receipt = SimpleNamespace(reason='transit waypoint passed', to_dict=lambda: {})
            return SimpleNamespace(receipt=receipt, observation=self.current)

    def review_input():
        if case == 'eof':
            raise EOFError
        return 'continue'

    monkeypatch.setattr('builtins.input', review_input)
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda value: value)
    monkeypatch.setattr(module, 'decode_result', lambda value: value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN', 'test-only')
    review = tmp_path/'review.json'
    review.write_text(json.dumps(dict(observation_id='other:0' if case == 'stale' else initial.key,
        decision='retreat', preserve_orientation=True, preserve_open_grip=True,
        translation_world_m=[0, 0, .031 if case == 'oversize' else .0028])))
    monkeypatch.setattr(module.sys, 'argv', ['test', '--url', 'http://unused',
        '--review', str(review), '--output', str(tmp_path/'out')])
    if case in ('stale', 'oversize'):
        with pytest.raises(ValueError):
            module.main()
        assert not calls
        return
    module.main()
    result = json.loads((tmp_path/'out'/'result.json').read_text())
    if case == 'complete':
        assert len(calls) == 2 and result['status'] == 'bounded_retreat_finished'
    elif case == 'eof':
        assert len(calls) == 1 and result['status'] == 'stopped_by_visual_review'
    else:
        assert len(calls) == (2 if case == 'stall' else 1)
        assert result['status'] == 'stopped_without_retry'
