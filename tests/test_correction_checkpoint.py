from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


def load_script(name):
    path = Path(__file__).resolve().parents[1]/'scripts'/f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(path.parent))
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('pause,terminal,grasp_only', [
    ('--pause-before-close','awaiting_preclosure_review',False),
    ('--pause-at-standoff','awaiting_close_range_target',False),
    ('--pause-before-close','awaiting_preclosure_review',True)])
def test_pause_before_close_never_sends_closure(monkeypatch, tmp_path, observation, pause, terminal, grasp_only):
    module = load_script('run_grounded_correction')
    initial = replace(observation, eef_pose=np.array([.18,-.34,.35,0,0,1,0]), gripper_open=1.)
    calls = []

    class Client:
        current = initial
        def __init__(self, *args, **kwargs):
            pass
        def close(self):
            pass
        def call(self, route, envelope=None, **kwargs):
            if route == '/metadata':
                return {'local_stages_enabled':True, 'real_hardware_supported':False}
            if route == '/observe':
                return self.current
            assert route == '/local-stage'
            action = envelope['action']
            assert action['observation_id'] == self.current.key
            calls.append(action)
            self.current = replace(self.current, seq=self.current.seq+64,
                                   eef_pose=np.asarray(action['hand_pose_world']))
            receipt = SimpleNamespace(reason='local stage arrived', to_dict=lambda: {'test_double':True,'executed_steps':64})
            return SimpleNamespace(receipt=receipt, observation=self.current)

    plan = tmp_path/'plan.json'
    plan.write_text(json.dumps({'observation_id':initial.key,
                    'target_source':'cached pixel on fresh depth',
                    'measured_surface':{'surface_point_world_m':[.18,-.34,.13]}}))
    output = tmp_path/'output'
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda value:value)
    monkeypatch.setattr(module, 'decode_result', lambda value:value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN','test-only')
    monkeypatch.setattr(module.sys, 'argv', ['test','--url','http://unused','--plan',str(plan),
                                           '--output',str(output),pause]
                        + (['--grasp-only','--lift-height','.23'] if grasp_only else []))
    module.main()
    assert calls and all(action['gripper_open'] == 1 for action in calls)
    assert all(action['target_source'].startswith('cached pixel on fresh depth') for action in calls)
    result = json.loads((output/'result.json').read_text())
    assert result['terminal_reason'] == terminal
    assert result['actions'] == 64*len(calls)
    assert result['grasp_verified'] is False
    if grasp_only:
        stages = json.loads((output/'declared_sequence.json').read_text())
        assert {s['name'] for s in stages} == {'descend','close','short_lift'}
        assert stages[-1]['hand_pose_world'][2] == pytest.approx(.13+.1034-.015+.23)


def test_exploratory_contact_nonarrival_does_not_retry(monkeypatch, tmp_path, observation):
    module = load_script('probe_contact_stage')
    calls = []
    class Client:
        def __init__(self, *args, **kwargs):
            pass
        def close(self):
            pass
        def call(self, route, envelope=None, **kwargs):
            if route == '/metadata':
                return {'local_stages_enabled':True, 'real_hardware_supported':False}
            if route == '/observe':
                return observation
            calls.append(envelope)
            receipt = SimpleNamespace(reason='local stage budget ended without arrival',
                                      to_dict=lambda: {'test_double':True})
            return SimpleNamespace(receipt=receipt, observation=observation)
    monkeypatch.setattr(module,'LocalClient',Client)
    monkeypatch.setattr(module,'decode_observation',lambda value:value)
    monkeypatch.setattr(module,'decode_result',lambda value:value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN','test-only')
    monkeypatch.setattr(module.sys,'argv',['test','--url','http://unused','--observation-id',observation.key,
                         '--mode','close','--output',str(tmp_path/'contact')])
    with pytest.raises(RuntimeError,match='no retry'):
        module.main()
    assert len(calls) == 1
    assert calls[0]['action']['max_steps'] == 64
    assert calls[0]['action']['hand_pose_world'] == observation.eef_pose.tolist()


def test_contact_motion_bounds_do_not_require_insertion_tolerance():
    module = load_script('probe_contact_stage')
    receipt = dict(status='executed',executed_steps=64,requested_steps=64,
                   tracking_position_error_m=.00235,tracking_rotation_error_rad=.041)
    assert module.exploratory_completion(receipt)
    for change in ({'tracking_rotation_error_rad':.16},{'tracking_position_error_m':.011},
                   {'executed_steps':63},{'status':'rejected'},{'tracking_rotation_error_rad':float('nan')}):
        assert not module.exploratory_completion({**receipt,**change})


def test_lift_review_requires_contiguous_probes(tmp_path):
    module = load_script('prepare_lift_review')
    close, lift = tmp_path/'close', tmp_path/'lift'
    close.mkdir()
    lift.mkdir()
    (close/'after.json').write_text(json.dumps({'observation_id':'episode:704'}))
    (lift/'before.json').write_text(json.dumps({'observation_id':'episode:704'}))
    captures = module.probe_captures(close, lift)
    assert [entry[0] for entry in captures] == ['before_closure','after_closure','after_lift']
    (lift/'before.json').write_text(json.dumps({'observation_id':'other:704'}))
    with pytest.raises(ValueError, match='not contiguous'):
        module.probe_captures(close, lift)
