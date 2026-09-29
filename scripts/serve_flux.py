#!/usr/bin/env python3
"""Run INSIDE FLUX's separate Python 3.12 GPU environment. No LLM API call."""
from pathlib import Path
import argparse
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint",required=True,help="local complete FLUX DROID package, with encoders cached")
    p.add_argument("--port",type=int,default=8766);p.add_argument("--device",default="cuda:0")
    p.add_argument("--compile",action="store_true",help="opt-in; start eager for qualification")
    p.add_argument("--gripper-boundary-tolerance",type=float,default=0.,
                   help="explicit experimental gripper saturation, at most 0.01; default strict")
    p.add_argument("--token-env",default="PHYSICAL_EXEC_FLUX_TOKEN")
    args=p.parse_args()
    token=os.environ.get(args.token_env,"")
    if len(token)<16: raise SystemExit(f"Set {args.token_env} to a fresh token")
    from physical_exec.backends.flux import FluxEngine
    from physical_exec.transport import make_server
    engine=FluxEngine(args.checkpoint,{"left":"left","right":"right","wrist":"wrist"},args.device,args.compile,
                      gripper_boundary_tolerance=args.gripper_boundary_tolerance)
    server=make_server(args.port,token,engine.dispatch)
    print(f"READY FLUX http://127.0.0.1:{server.server_port}; eager={not args.compile}",flush=True)
    try: server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__": main()
