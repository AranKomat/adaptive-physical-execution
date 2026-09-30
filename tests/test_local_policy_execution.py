import json
import numpy as np
import pytest

from physical_exec.backends.fixture import FixtureEnvironment
from physical_exec.contracts import ExecutionReceipt, StepResult
from physical_exec.runner import run_episode,RunBudget
from physical_exec.trace import verify_trace
from test_runner_transport import controller


@pytest.mark.parametrize('mode',['direct_roboicl','direct_reference','hybrid'])
@pytest.mark.parametrize('stop',[False,True])
def test_local_policy_actual_budget_and_stop(tmp_path,mode,stop):
    class Env(FixtureEnvironment):
        local_calls=0
        def metadata(self):
            return {**super().metadata(),'local_stages_enabled':True,'contact_tracking_guard_enabled':True}
        def local_stage(self,request,cid):
            self.local_calls+=1
            before=self._observe()
            assert request['max_steps']==7
            self.seq+=7
            self.pose=np.array(request['hand_pose_world'])
            after=self._observe()
            return StepResult(after,ExecutionReceipt(cid,before.key,after.key,7,7,'executed',
                'contact tracking guard stopped motion' if stop else 'local stage arrived',
                'sensor_local_diffik',7/15,.01),self.evaluate())
    env=Env(complete_after=100)
    ctrl=controller(mode)
    ctrl.horizon=1
    run=run_episode(env,ctrl,tmp_path/'run',0,RunBudget(5,7,60),local_eef_execution=True)
    result=json.loads((run/'result.json').read_text())
    if mode=='hybrid':
        # Fixture hybrid accepts native joint proposals; local routing must not rewrite them.
        assert env.local_calls==0
    else:
        assert env.local_calls==1
        assert result['executed_control_steps']==7
        assert result['terminal_reason']==('local_stage_stopped_without_retry' if stop else 'control_budget')
        assert 'receipt counts local control actions' in str(ctrl.memory.records)
    verify_trace(run)
