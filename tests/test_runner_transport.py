from dataclasses import replace
import json
from pathlib import Path
import socket
import threading
import numpy as np
import pytest
import httpx
from physical_exec.backends.fixture import FixtureEnvironment,FixtureProvider,FixtureProposer
from physical_exec.controllers.ports import ControllerPort
from physical_exec.memory import ExecutionMemory,MemoryConfig,reference_from_run
from physical_exec.runner import run_episode,RunBudget
from physical_exec.safety import Limits
from physical_exec.contracts import ActionChunk,Evaluation
from physical_exec.errors import AmbiguousExecution,InputRejected,ProtocolError
from physical_exec.transport import make_server,EnvironmentService,LocalClient,RemoteEnvironment
from physical_exec.trace import verify_trace,dumps
from physical_exec.reports import render_html,compare_runs

TOKEN='test-token-at-least-sixteen'

def controller(mode='direct_roboicl',provider=None):
    return ControllerPort(mode,provider or FixtureProvider(),ExecutionMemory(MemoryConfig(),60),Limits(),3,
                          FixtureProposer() if mode=='hybrid' else None)

def run_fixture(tmp_path,mode='direct_roboicl',env=None,provider=None,budget=None):
    return run_episode(env or FixtureEnvironment(),controller(mode,provider),tmp_path/mode,0,budget or RunBudget(20,60,60),
                       {'model':'SOFTWARE_FIXTURE','reasoning_effort':'none'})

@pytest.mark.parametrize('mode',['direct_roboicl','direct_reference','hybrid'])
def test_runner_end_to_end(mode,tmp_path):
    run=run_fixture(tmp_path,mode)
    result=json.loads((run/'result.json').read_text())
    assert result['fixture_pass'] and not result['native_success'] and not result['valid_robot_result']
    assert result['usage']['calls']==0 and result['executed_control_steps']==12
    assert verify_trace(run)['events']>15
    assert 'SOFTWARE FIXTURE' in render_html(run).read_text()
    with pytest.raises(ValueError):reference_from_run(run,'fixture_arm','anything')


def test_ambiguous_execution_not_retried(tmp_path):
    class Broken(FixtureEnvironment):
        calls=0
        def step(self,a,c):
            self.calls+=1;super().step(a,c);raise AmbiguousExecution('uncertain ack')
    env=Broken();run=run_fixture(tmp_path,env=env)
    assert env.calls==1
    r=json.loads((run/'result.json').read_text());assert r['terminal_reason']=='ambiguous_execution_halted'
    assert not r['valid_robot_result']


def test_privileged_evaluation_sentinel_never_in_model_messages(tmp_path):
    class HostOnly(FixtureEnvironment):
        def evaluate(self):
            return Evaluation(self.seq>=self.complete_after,.918273645,False,'SECRET_EVALUATOR_SENTINEL')
    class Watching(FixtureProvider):
        def act(self,prompt,messages,*a,**k):
            text=dumps(messages)+prompt
            assert 'SECRET_EVALUATOR_SENTINEL' not in text
            assert '.918273645' not in text
            return super().act(prompt,messages,*a,**k)
    run=run_fixture(tmp_path,env=HostOnly(),provider=Watching())
    assert 'SECRET_EVALUATOR_SENTINEL' in (run/'events.jsonl').read_text()


def test_rejection_retries_do_not_reset_or_move(tmp_path):
    class Bad(FixtureProvider):
        def act(self,*a,**k):
            reply=super().act(*a,**k);reply.arguments['observation_id']='wrong';return reply
    env=FixtureEnvironment();run=run_fixture(tmp_path,env=env,provider=Bad())
    assert env.seq==0
    r=json.loads((run/'result.json').read_text());assert r['rejections']==3 and r['terminal_reason']=='rejection_budget'


def test_budget_explicit_prefix_and_no_success(tmp_path):
    run=run_fixture(tmp_path,budget=RunBudget(30,2,60))
    r=json.loads((run/'result.json').read_text())
    assert r['executed_control_steps']==2 and not r['native_success']
    assert 'host_prefix_limit' in (run/'events.jsonl').read_text()


def test_trace_detects_modified_result_manifest_image(tmp_path):
    run=run_fixture(tmp_path)
    original=(run/'result.json').read_text();r=json.loads(original);r['native_success']=True
    (run/'result.json').write_text(json.dumps(r))
    with pytest.raises(ValueError):verify_trace(run)
    (run/'result.json').write_text(original)
    original=(run/'manifest.json').read_text();m=json.loads(original);m['robot']='pretend'
    (run/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError):verify_trace(run)
    (run/'manifest.json').write_text(original)
    p=next((run/'frames').glob('*.png'));p.write_bytes(b'changed')
    with pytest.raises(ValueError):verify_trace(run)


def test_report_escapes_model_prose(tmp_path):
    class HTMLProvider(FixtureProvider):
        def act(self,*a,**k):
            r=super().act(*a,**k);r.arguments['intent']='<script>alert(1)</script>';return r
    run=run_fixture(tmp_path,provider=HTMLProvider());text=render_html(run).read_text()
    assert '<script>alert(1)' not in text and '&lt;script&gt;' in text


def test_compare_preserves_attempts_and_fixture_status(tmp_path):
    a=run_fixture(tmp_path/'a');b=run_fixture(tmp_path/'b',budget=RunBudget(1,60,60))
    out=compare_runs([a,b],tmp_path/'comparison');obj=json.loads((out/'runs.json').read_text())
    assert len(obj['runs'])==2 and all(not r['native_success'] for r in obj['runs'])


def test_service_idempotence_reset_ban_and_privileged_rpc_ban():
    env=FixtureEnvironment();s=EnvironmentService(env);data=s.dispatch('/reset',{'seed':1})
    o=env._observe();a=ActionChunk('eef_delta_world',[[.01,0,0,0,0,0,.7]],o.key,o.control_dt,'test')
    msg={'command_id':'c','action':a.to_dict()}
    first=s.dispatch('/step',msg);second=s.dispatch('/step',msg)
    assert first==second and env.seq==1
    with pytest.raises(InputRejected):s.dispatch('/reset',{'seed':2})
    with pytest.raises(InputRejected):s.dispatch('/object_pose',{})
    changed=json.loads(dumps(msg));changed['action']['values'][0][0]=.02
    with pytest.raises(InputRejected):s.dispatch('/step',changed)


def test_fixture_delta_idempotence():
    env=FixtureEnvironment();o=env.reset(0)
    a=ActionChunk('eef_delta_world',[[.01,0,0,0,0,0,.5]],o.key,o.control_dt,'test')
    first=env.step(a,'x');assert env.step(a,'x') is first and env.seq==1


def test_real_loopback_transport(tmp_path):
    server=make_server(0,TOKEN,EnvironmentService(FixtureEnvironment()).dispatch)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}'
    try:
        with httpx.Client(trust_env=False) as c:
            assert c.post(url+'/metadata',json={}).status_code==401
        remote=RemoteEnvironment(LocalClient(url,TOKEN))
        run=run_fixture(tmp_path,env=remote)
        assert json.loads((run/'result.json').read_text())['fixture_pass']
    finally:
        server.shutdown();server.server_close();thread.join(3)


def test_mutating_http_timeout_is_ambiguous_no_retry():
    calls=[]
    def handler(req):calls.append(1);raise httpx.ReadTimeout('test')
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        client=LocalClient('http://127.0.0.1:8765',TOKEN,client=c)
        with pytest.raises(AmbiguousExecution):client.call('/step',{},mutating=True)
        assert len(calls)==1

@pytest.mark.parametrize('url',['http://public.example:80','https://127.0.0.1:80','http://u:p@127.0.0.1:80'])
def test_workers_are_loopback_only(url):
    with pytest.raises(ValueError):LocalClient(url,TOKEN)


def test_service_reset_failure_cannot_be_retried():
    class Broken(FixtureEnvironment):
        def reset(self,seed):raise RuntimeError('partially initialized')
    s=EnvironmentService(Broken())
    with pytest.raises(RuntimeError):s.dispatch('/reset',{'seed':0})
    with pytest.raises(InputRejected):s.dispatch('/reset',{'seed':0})
