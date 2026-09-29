"""Operator CLI. A live model request always requires --allow-paid."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
from .config import load_task
from .memory import ExecutionMemory, MemoryConfig
from .controllers.ports import ControllerPort
from .safety import Limits
from .runner import run_episode, RunBudget
from .trace import write_json, verify_trace
from .reports import render_html, compare_runs

MODES = ("direct_roboicl", "direct_reference", "hybrid")


def token(name):
    value=os.environ.get(name,"")
    if len(value)<16: raise ValueError(f"Set {name} to an independently generated token of at least 16 characters")
    return value


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    d=sub.add_parser("doctor",help="offline environment/dependency inspection; no network or simulator")
    d.add_argument("--task");d.add_argument("--upstream-root",default="upstream")
    s=sub.add_parser("smoke",help="CPU software fixtures only; no robotics success or API calls")
    s.add_argument("--output",required=True);s.add_argument("--mode",choices=(*MODES,"all"),default="all")
    v=sub.add_parser("verify-trace");v.add_argument("run")
    h=sub.add_parser("report");h.add_argument("run");h.add_argument("--output")
    c=sub.add_parser("compare");c.add_argument("runs",nargs="+");c.add_argument("--output",required=True)
    cap=sub.add_parser("capture",help="reset a fresh simulator worker and save sensor views, no model request")
    cap.add_argument("--sim-url",default="http://127.0.0.1:8765");cap.add_argument("--sim-token-env",default="PHYSICAL_EXEC_SIM_TOKEN")
    cap.add_argument("--seed",type=int,default=0);cap.add_argument("--output",required=True)
    pr=sub.add_parser("probe-flux",help="run FLUX on the current captured simulator observation; NEVER execute it")
    pr.add_argument("--sim-url",default="http://127.0.0.1:8765");pr.add_argument("--sim-token-env",default="PHYSICAL_EXEC_SIM_TOKEN")
    pr.add_argument("--flux-url",default="http://127.0.0.1:8766");pr.add_argument("--flux-token-env",default="PHYSICAL_EXEC_FLUX_TOKEN")
    pr.add_argument("--task",required=True);pr.add_argument("--output",required=True)
    r=sub.add_parser("run",help="run one live-model simulation episode on a fresh worker")
    r.add_argument("--task",required=True);r.add_argument("--mode",choices=MODES,required=True)
    r.add_argument("--output",required=True);r.add_argument("--seed",type=int,default=0)
    r.add_argument("--sim-url",default="http://127.0.0.1:8765");r.add_argument("--sim-token-env",default="PHYSICAL_EXEC_SIM_TOKEN")
    r.add_argument("--flux-url",default="http://127.0.0.1:8766");r.add_argument("--flux-token-env",default="PHYSICAL_EXEC_FLUX_TOKEN")
    r.add_argument("--ack-experimental-flux",action="store_true")
    r.add_argument("--model",required=True,help="exact model ID authorized on YOUR chosen endpoint")
    r.add_argument("--endpoint",required=True,help="complete https://.../responses; never inherited from upstream")
    r.add_argument("--key-env",default="OPENAI_API_KEY");r.add_argument("--allow-paid",action="store_true")
    r.add_argument("--reasoning",choices=("low","medium","high","xhigh"),default="medium")
    r.add_argument("--horizon",type=int);r.add_argument("--memory",choices=("anchored","full"))
    r.add_argument("--max-images",type=int,default=50);r.add_argument("--image-edge",type=int,default=640)
    r.add_argument("--max-decisions",type=int,default=100);r.add_argument("--max-control-steps",type=int,default=1800)
    r.add_argument("--max-wall-seconds",type=float,default=1800);r.add_argument("--max-total-tokens",type=int,default=20_000_000)
    r.add_argument("--request-timeout",type=float,default=180);r.add_argument("--max-output-tokens",type=int,default=8192)
    r.add_argument("--reference-run");r.add_argument("--allow-related-reference",action="store_true")
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=="doctor":
            data={"python":sys.version,"platform":platform.platform(),"scope":"CPU/offline checks only",
                  "dependencies":{x:bool(importlib.util.find_spec(x)) for x in ("numpy","PIL","httpx","torch","isaaclab","flux_action")},
                  "upstream":{x:(Path(args.upstream_root)/x).exists() for x in ("RoboICL","GPT-as-Policy","flux-action","EmbodiedSWE")},
                  "credentials":{x:"set" if os.environ.get(x) else "not set" for x in ("OPENAI_API_KEY","PHYSICAL_EXEC_SIM_TOKEN","PHYSICAL_EXEC_FLUX_TOKEN")}}
            if args.task:
                task,limits=load_task(args.task);data["task"]={"id":task["id"],"preset":task["preset"],"limits":asdict(limits)}
            print(json.dumps(data,indent=2));return 0
        if args.command=="smoke":
            from .backends.fixture import FixtureEnvironment, FixtureProvider, FixtureProposer
            root=Path(args.output);root.mkdir(parents=True,exist_ok=False)
            modes=MODES if args.mode=="all" else (args.mode,)
            for mode in modes:
                memory=ExecutionMemory(MemoryConfig(mode="full" if mode=="direct_reference" else "anchored"),maximum_steps=60)
                limits=Limits();ctrl=ControllerPort(mode,FixtureProvider(),memory,limits,horizon=3,
                                                   proposer=FixtureProposer() if mode=="hybrid" else None)
                run=run_episode(FixtureEnvironment(limits),ctrl,root/mode,0,RunBudget(20,60,60),
                                {"model":"SOFTWARE_FIXTURE","reasoning_effort":"none"})
                verify_trace(run);render_html(run)
                result=json.loads((run/"result.json").read_text())
                if not result["fixture_pass"]: raise RuntimeError(f"fixture failed: {result}")
            print(f"CPU fixtures passed; NOT a robotics result. Reports: {root.resolve()}");return 0
        if args.command=="verify-trace": print(json.dumps(verify_trace(args.run),indent=2));return 0
        if args.command=="report": print(render_html(args.run,args.output));return 0
        if args.command=="compare": print(compare_runs(args.runs,args.output));return 0
        from .transport import LocalClient, RemoteEnvironment
        if args.command=="capture":
            from .imaging import png_bytes
            out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
            env=RemoteEnvironment(LocalClient(args.sim_url,token(args.sim_token_env)))
            try:
                obs=env.reset(args.seed)
                write_json(out/"metadata.json",env.metadata());write_json(out/"observation.json",obs.public_state())
                for i,(role,image) in enumerate(obs.images.items()):
                    (out/f"camera_{i}.png").write_bytes(png_bytes(image))
                write_json(out/"camera_index.json",{f"camera_{i}.png":role for i,role in enumerate(obs.images)})
            finally: env.close()
            print(f"Sensor capture saved to {out}. Restart the simulator worker before an actual episode.");return 0
        if args.command=="probe-flux":
            from .transport import decode_observation
            from .backends.flux import RemoteFluxProposer
            from .safety import validate_chunk
            task,limits=load_task(args.task)
            out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
            env=RemoteEnvironment(LocalClient(args.sim_url,token(args.sim_token_env)))
            proposer=None
            try:
                if env.metadata().get("preset")!=task["preset"]: raise ValueError("worker/task mismatch")
                obs=decode_observation(env.client.call("/observe"))
                proposer=RemoteFluxProposer(LocalClient(args.flux_url,token(args.flux_token_env),timeout=180),env)
                proposer.qualification_acknowledged=True
                proposal=proposer.propose(obs)
                report=proposal.public()
                try:
                    validate_chunk(proposal.action,obs,limits)
                    report["generic_bounds_pass"]=True
                except Exception as e:
                    report["generic_bounds_pass"]=False;report["rejection"]=str(e)
                report["executed"]=False
                report["limitation"]="Shape/FK/bounds probe only. No evidence of task competence, collision safety or sim-to-real transfer."
                write_json(out/"proposal.json",report);print(out/"proposal.json")
            finally:
                env.close()
                if proposer: proposer.close()
            return 0 if report["generic_bounds_pass"] else 2
        if args.command=="run":
            if not args.allow_paid: raise ValueError("No paid model call authorized. Pass --allow-paid explicitly.")
            if args.mode=="hybrid" and not args.ack_experimental_flux:
                raise ValueError("Hybrid requires --ack-experimental-flux after sensor/FK/action qualification")
            task,limits=load_task(args.task)
            from .providers.responses import ProviderConfig, ResponsesProvider
            cfg=ProviderConfig(args.model,args.endpoint,args.key_env,args.reasoning,args.request_timeout,
                               args.max_output_tokens,args.max_decisions,args.max_total_tokens)
            env=RemoteEnvironment(LocalClient(args.sim_url,token(args.sim_token_env),timeout=180))
            if env.metadata().get("preset") != task["preset"]:
                env.close();raise ValueError("task preset does not match running simulator")
            proposer=None
            if args.mode=="hybrid":
                from .backends.flux import RemoteFluxProposer
                proposer=RemoteFluxProposer(LocalClient(args.flux_url,token(args.flux_token_env),timeout=180),env)
                proposer.qualification_acknowledged=True
            provider=ResponsesProvider(cfg,allow_paid=True)
            memory=ExecutionMemory(MemoryConfig(mode=args.memory or ("full" if args.mode=="direct_reference" else "anchored"),
                                                  max_images=args.max_images,image_edge=args.image_edge),args.max_control_steps)
            horizon=args.horizon or task["default_horizons"][args.mode]
            controller=ControllerPort(args.mode,provider,memory,limits,horizon,proposer)
            out=run_episode(env,controller,args.output,args.seed,
                            RunBudget(args.max_decisions,args.max_control_steps,args.max_wall_seconds),
                            {"model":args.model,"reasoning_effort":args.reasoning,"endpoint":args.endpoint,
                             "task_config_path":str(Path(args.task).resolve()),
                             "model_output_token_cap":args.max_output_tokens},
                            reference_run=args.reference_run,allow_related_reference=args.allow_related_reference)
            render_html(out)
            result=json.loads((out/"result.json").read_text())
            print(json.dumps(result,indent=2))
            return 0 if result["native_success"] else 2
    except (ValueError,RuntimeError,OSError) as e:
        print(f"ERROR: {type(e).__name__}: {e}",file=sys.stderr);return 2
    return 0

if __name__=="__main__": raise SystemExit(main())
