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


@pytest.mark.parametrize('continuous', [True, False])
@pytest.mark.parametrize('pause,terminal,grasp_only', [
    ('--pause-before-close','awaiting_preclosure_review',False),
    ('--pause-at-standoff','awaiting_close_range_target',False),
    ('--pause-before-close','awaiting_preclosure_review',True),
    ('--approach-only',None,False), ('--preclosure-only',None,False)])
def test_pause_before_close_never_sends_closure(monkeypatch, tmp_path, observation, pause, terminal, grasp_only, continuous):
    module = load_script('run_grounded_correction')
    initial = replace(observation, eef_pose=np.array([.18,-.34,.35,0,0,1,0]), gripper_open=1.)
    if pause == '--approach-only':
        initial = replace(initial, eef_pose=np.array([.18,-.34,.5,0,1,0,0]))
    calls = []

    class Client:
        current = initial
        def __init__(self, *args, **kwargs):
            pass
        def close(self):
            pass
        def call(self, route, envelope=None, **kwargs):
            if route == '/metadata':
                return {'local_stages_enabled':True, 'real_hardware_supported':False,
                        'continuous_transit_enabled':True, 'contact_tracking_guard_enabled':True}
            if route == '/observe':
                return self.current
            assert route == '/local-stage'
            action = envelope['action']
            assert action['observation_id'] == self.current.key
            calls.append(action)
            self.current = replace(self.current, seq=self.current.seq+64,
                                   eef_pose=np.asarray(action['hand_pose_world']))
            receipt = SimpleNamespace(reason=('transit waypoint passed' if action.get('settle_at_end') is False
                                              else 'local stage arrived'),
                                      to_dict=lambda: {'test_double':True,'executed_steps':64})
            return SimpleNamespace(receipt=receipt, observation=self.current)

    plan = tmp_path/'plan.json'
    plan.write_text(json.dumps({'observation_id':initial.key,
                    'target_source':'cached pixel on fresh depth',
                    'bite_depth_m':.005,
                    'target_hand_pose_world':[.18,-.34,.13+.1034-.005,0,0,1,0],
                    'measured_surface':{'surface_point_world_m':[.18,-.34,.13]}}))
    review = tmp_path/'review.json'
    review.write_text(json.dumps({'observation_id':initial.key, 'decision':'approve_preclosure',
                                 'contact_authorized':False}))
    if pause == '--preclosure-only':
        from physical_exec.kinematics import URDFKinematics
        fake_kin = SimpleNamespace(fk=lambda q: [0,0,0,1,0,0,0],
            solve=lambda *a,**kw: SimpleNamespace(converged=True,joints=initial.joints))
        monkeypatch.setattr(URDFKinematics,'from_urdf',lambda *a:fake_kin)
    output = tmp_path/'output'
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda value:value)
    monkeypatch.setattr(module, 'decode_result', lambda value:value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN','test-only')
    monkeypatch.setattr(module.sys, 'argv', ['test','--url','http://unused','--plan',str(plan),
                                           '--output',str(output),pause]
                        + (['--grasp-only','--lift-height','.23'] if grasp_only else [])
                        + (['--contact-tracking-guard'] if pause in ('--approach-only','--preclosure-only') else [])
                        + (['--preclosure-review',str(review)] if pause == '--preclosure-only' else [])
                        + ([] if continuous else ['--no-continuous-transit']))
    module.main()
    assert calls and all(action['gripper_open'] == 1 for action in calls)
    assert all(action['target_source'].startswith('cached pixel on fresh depth') for action in calls)
    result = json.loads((output/'result.json').read_text())
    if terminal is not None:
        assert result['terminal_reason'] == terminal
    assert result['actions'] == 64*len(calls)
    assert result['grasp_verified'] is False
    stages = json.loads((output/'declared_sequence.json').read_text())
    if pause == '--approach-only':
        assert len(calls) <= 8
        assert {s['name'] for s in stages} == {'standoff'}
        assert all(np.allclose(s['hand_pose_world'][3:], initial.eef_pose[3:]) for s in stages)
        assert all(action['contact_tracking_guard'] for action in calls)
    if pause == '--preclosure-only':
        assert {s['name'] for s in stages} == {'reorient','preclosure'}
        assert stages[-1]['hand_pose_world'][2] == pytest.approx(.13+.1034-.005)
        assert all(action['contact_tracking_guard'] for action in calls)
    if continuous:
        assert any(s['settle_at_end'] is False for s in stages)
        for i, stage in enumerate(stages):
            assert stage['settle_at_end'] == (i == len(stages)-1
                or stages[i+1]['name'] != stage['name'] or stage['name'] == 'close')
    else:
        assert all('settle_at_end' not in s for s in stages)
    if grasp_only:
        stages = json.loads((output/'declared_sequence.json').read_text())
        assert {s['name'] for s in stages} == {'descend','close','short_lift'}
        assert stages[-1]['hand_pose_world'][2] == pytest.approx(.13+.1034-.015+.23)


@pytest.mark.parametrize('reviewed', [False, True])
def test_exploratory_contact_nonarrival_does_not_retry(monkeypatch, tmp_path, observation, reviewed):
    module = load_script('probe_contact_stage')
    calls = []
    class Client:
        def __init__(self, *args, **kwargs):
            pass
        def close(self):
            pass
        def call(self, route, envelope=None, **kwargs):
            if route == '/metadata':
                return {'local_stages_enabled':True, 'real_hardware_supported':False,
                        'contact_tracking_guard_enabled':True}
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
    review = tmp_path/'close_review.json'
    review.write_text(json.dumps({'observation_id':observation.key, 'decision':'close_candidate'}))
    monkeypatch.setattr(module.sys,'argv',['test','--url','http://unused','--observation-id',observation.key,
                         '--mode','close','--output',str(tmp_path/'contact')]
                        + (['--opening','.05','--contact-tracking-guard','--review',str(review)] if reviewed else []))
    with pytest.raises(RuntimeError,match='no retry'):
        module.main()
    assert len(calls) == 1
    assert calls[0]['action']['max_steps'] == 64
    assert calls[0]['action']['hand_pose_world'] == observation.eef_pose.tolist()
    assert calls[0]['action']['gripper_open'] == (.05 if reviewed else .3)
    if reviewed:
        assert calls[0]['action']['contact_tracking_guard'] is True


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
