"""Reference serialization tests use a NATIVE-INTERFACE TEST DOUBLE only.
No artifacts from these tests are shipped as real simulator outcomes.
"""
from pathlib import Path
import json
import pytest
from physical_exec.backends.fixture import FixtureEnvironment,FixtureProvider
from physical_exec.contracts import Evaluation
from physical_exec.controllers.ports import ControllerPort
from physical_exec.memory import ExecutionMemory,MemoryConfig,reference_from_run
from physical_exec.runner import run_episode,RunBudget
from physical_exec.safety import Limits
from physical_exec.trace import dumps

class NativeInterfaceDouble(FixtureEnvironment):
    def metadata(self):
        m=super().metadata();m['backend']='embodiedswe';m['test_double']=True;return m
    def evaluate(self):return Evaluation(self.seq>=self.complete_after,.99172,True,'NATIVE_INTERFACE_TEST_SENTINEL')

def test_reference_trace_reuse_and_matching_contract(tmp_path):
    def run(out,reference=None):
        c=ControllerPort('direct_roboicl',FixtureProvider(),ExecutionMemory(MemoryConfig(),60),Limits(),3)
        return run_episode(NativeInterfaceDouble(),c,out,0,RunBudget(20,60,60),reference_run=reference),c
    first,_=run(tmp_path/'first')
    task=json.loads((first/'manifest.json').read_text())['task_instruction']
    refs=reference_from_run(first,'fixture_arm',task,expected_dt=1/15,expected_eef_frame='fixture_eef')
    assert 'NATIVE_INTERFACE_TEST_SENTINEL' not in dumps(refs)
    assert '0.99172' not in dumps(refs)
    assert 'TRAIN_REFERENCE' in dumps(refs)
    second,c=run(tmp_path/'second',first)
    assert c.memory.references and json.loads((second/'result.json').read_text())['native_success']
    for kwargs in [{'expected_dt':.1},{'expected_eef_frame':'wrong'},{'max_chunks':0}]:
        with pytest.raises(ValueError):reference_from_run(first,'fixture_arm',task,**kwargs)
    with pytest.raises(ValueError):reference_from_run(first,'wrong_robot',task)


def test_success_at_reset_does_not_count_as_controller_success(tmp_path):
    class AlreadyDone(NativeInterfaceDouble):
        def evaluate(self):return Evaluation(True,1.0,True,'TEST RESET ALREADY COMPLETE')
    c=ControllerPort('direct_roboicl',FixtureProvider(),ExecutionMemory(MemoryConfig(),60),Limits(),3)
    out=run_episode(AlreadyDone(),c,tmp_path/'already_done',0,RunBudget(20,60,60))
    r=json.loads((out/'result.json').read_text())
    assert r['terminal_reason']=='already_terminal_at_reset'
    assert r['environment_success_host_only'] and not r['native_success'] and not r['valid_robot_result']
