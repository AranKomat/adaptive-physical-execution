from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def load_script(name):
    path = Path(__file__).resolve().parents[1]/'scripts'/f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pause_before_close_never_sends_closure(monkeypatch, tmp_path, observation):
    module = load_script('run_grounded_correction')
    initial = replace(observation, eef_pose=np.array([.18,-.34,.35,0,0,1,0]))
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
            receipt = SimpleNamespace(reason='local stage arrived', to_dict=lambda: {'test_double':True})
            return SimpleNamespace(receipt=receipt, observation=self.current)

    plan = tmp_path/'plan.json'
    plan.write_text(json.dumps({'observation_id':initial.key,
                    'measured_surface':{'surface_point_world_m':[.18,-.34,.13]}}))
    output = tmp_path/'output'
    monkeypatch.setattr(module, 'LocalClient', Client)
    monkeypatch.setattr(module, 'decode_observation', lambda value:value)
    monkeypatch.setattr(module, 'decode_result', lambda value:value)
    monkeypatch.setenv('PHYSICAL_EXEC_SIM_TOKEN','test-only')
    monkeypatch.setattr(module.sys, 'argv', ['test','--url','http://unused','--plan',str(plan),
                                           '--output',str(output),'--pause-before-close'])
    module.main()
    assert calls and all(action['gripper_open'] == 1 for action in calls)
    result = json.loads((output/'result.json').read_text())
    assert result['terminal_reason'] == 'awaiting_preclosure_review'
    assert result['actions'] == 64*len(calls)
    assert result['grasp_verified'] is False
