#!/usr/bin/env python3
"""Bounded sequential experiment campaign, with a fresh simulator per episode.

Plan-only by default. --execute AND --allow-paid are both required. All started
processes are owned process groups; cleanup never kills unrelated workloads.
Start a FLUX worker separately if hybrid is in the matrix. No reroll-on-failure.
"""
from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from physical_exec.transport import LocalClient
from physical_exec.config import load_task
from physical_exec.trace import write_json


def stop_owned(p):
    if p is None or p.poll() is not None:return
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(15)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);p.wait()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sim-python',required=True);p.add_argument('--sim-repo',required=True)
    p.add_argument('--tasks',nargs='+',default=['configs/tasks/pc_gpu.json','configs/tasks/pc_ram.json'])
    p.add_argument('--modes',nargs='+',choices=['direct_roboicl','direct_reference','hybrid'],default=['direct_roboicl','hybrid'])
    p.add_argument('--seeds',nargs='+',type=int,default=[0]);p.add_argument('--reasoning',nargs='+',choices=['medium','high','xhigh'],default=['medium'])
    p.add_argument('--model',required=True);p.add_argument('--endpoint',required=True);p.add_argument('--key-env',default='OPENAI_API_KEY')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8765)
    p.add_argument('--flux-url',default='http://127.0.0.1:8766')
    p.add_argument('--max-decisions',type=int,default=50);p.add_argument('--max-wall-seconds',type=int,default=900)
    p.add_argument('--startup-timeout',type=int,default=900)
    p.add_argument('--execute',action='store_true');p.add_argument('--allow-paid',action='store_true')
    p.add_argument('--ack-experimental-flux',action='store_true')
    a=p.parse_args()
    from physical_exec.providers.responses import ProviderConfig
    ProviderConfig(a.model,a.endpoint)
    cases=[]
    for taskfile in a.tasks:
        path=Path(taskfile).resolve();task,_=load_task(path)
        for mode in a.modes:
            for effort in a.reasoning:
                for seed in a.seeds:
                    cases.append({'id':f'{task["id"]}__{mode}__{effort}__s{seed}',
                                  'task':str(path),'mode':mode,'effort':effort,'seed':seed})
    print(json.dumps({'cases':cases,'max_model_decisions':len(cases)*a.max_decisions,
                      'wall_budget_per_case':a.max_wall_seconds,'cost_estimate':None},indent=2))
    if not a.execute:
        print('Plan only; add --execute --allow-paid after individual qualification.');return
    if not a.allow_paid:raise SystemExit('--allow-paid is required')
    if 'hybrid' in a.modes and not a.ack_experimental_flux:raise SystemExit('--ack-experimental-flux is required')
    token=os.environ.get('PHYSICAL_EXEC_SIM_TOKEN','')
    if len(token)<16:raise SystemExit('Set PHYSICAL_EXEC_SIM_TOKEN')
    if not os.environ.get(a.key_env):raise SystemExit(f'Set {a.key_env}')
    a.output.mkdir(parents=True,exist_ok=False);write_json(a.output/'plan.json',{'cases':cases})
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')+os.pathsep+os.environ.get('PYTHONPATH','')}
    ledger=[]
    for case in cases:
        directory=a.output/case['id'];directory.mkdir()
        sim=None;run=None;status={'id':case['id'],'status':'not_started'}
        worker_id=__import__('uuid').uuid4().hex
        worker_env={**env,'PHYSICAL_EXEC_WORKER_ID':worker_id}
        try:
            command=[a.sim_python,str(ROOT/'scripts/serve_embodiedswe.py'),'--repo',str(Path(a.sim_repo).resolve()),
                     '--task',case['task'],'--port',str(a.port),'--record-dir',str(directory/'recordings'),'--headless']
            with (directory/'simulator.log').open('w') as log:
                sim=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=worker_env,start_new_session=True)
                start=time.monotonic();ready=False
                while time.monotonic()-start<a.startup_timeout:
                    if sim.poll() is not None:raise RuntimeError('Simulator exited during startup; inspect simulator.log')
                    client=LocalClient(f'http://127.0.0.1:{a.port}',token,timeout=2)
                    try:
                        metadata=client.call('/metadata')
                        if metadata.get('worker_id')!=worker_id or metadata.get('preset')!=load_task(case['task'])[0]['preset']:
                            raise RuntimeError('Another worker is using the requested port')
                        ready=True;break
                    except Exception:time.sleep(1)
                    finally:client.close()
                if not ready:raise TimeoutError('Simulator startup timeout')
                args=[sys.executable,'-m','physical_exec','run','--task',case['task'],'--mode',case['mode'],
                      '--seed',str(case['seed']),'--reasoning',case['effort'],'--model',a.model,'--endpoint',a.endpoint,
                      '--key-env',a.key_env,'--sim-url',f'http://127.0.0.1:{a.port}',
                      '--flux-url',a.flux_url,'--max-decisions',str(a.max_decisions),
                      '--max-wall-seconds',str(a.max_wall_seconds),'--output',str(directory/'run'),'--allow-paid']
                if case['mode']=='hybrid':args.append('--ack-experimental-flux')
                with (directory/'controller.log').open('w') as runlog:
                    run=subprocess.Popen(args,stdout=runlog,stderr=subprocess.STDOUT,env=env,start_new_session=True)
                    try:
                        rc=run.wait(a.max_wall_seconds+240)
                        status.update(status='finished',returncode=rc)
                    except subprocess.TimeoutExpired:
                        stop_owned(run);status.update(status='external_watchdog_timeout',returncode=None)
        except KeyboardInterrupt:
            status.update(status='operator_interrupted');raise
        except Exception as e:
            status.update(status='infrastructure_error',error=f'{type(e).__name__}: {e}')
        finally:
            stop_owned(run);stop_owned(sim)
            ledger.append(status);write_json(a.output/'campaign.json',{'attempts':ledger,'no_automatic_retries':True})
    print(a.output/'campaign.json')

if __name__=='__main__':main()
