#!/usr/bin/env python3
"""Run INSIDE the upstream Isaac/EmbodiedSWE Python 3.11 environment.

No model API is used here. One episode per process. Only loopback is exposed.
"""
from pathlib import Path
import argparse
import os
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True);p.add_argument("--task",required=True)
    p.add_argument("--port",type=int,default=8765);p.add_argument("--record-dir",required=True)
    p.add_argument("--token-env",default="PHYSICAL_EXEC_SIM_TOKEN")
    p.add_argument("--record-depth",action="store_true",help="record aligned idealized depth/calibration; not yet policy input")
    p.add_argument("--allow-local-stages",action="store_true",help="opt-in bounded same-episode native-DiffIK correction; unknown clearance")
    p.add_argument("--local-stage-rotation-integral",action="store_true",help="experimental bounded rotation-integral feedback; default off")
    p.add_argument("--allow-inspection-camera",action="store_true",help="opt-in idealized right-camera movement during arm hold; requires local stages and recorded depth")
    # Import-light CLI help is available before Isaac is installed.
    if "--help" in sys.argv and __import__('importlib.util').util.find_spec("isaaclab") is None:
        p.add_argument("--headless",action="store_true");p.add_argument("--device",default="cuda:0")
        p.print_help();return
    if os.environ.get("OMNI_KIT_ACCEPT_EULA","").upper() not in ("YES","Y","1","TRUE"):
        raise SystemExit("Review Isaac Sim's terms and set OMNI_KIT_ACCEPT_EULA yourself. This launcher does not accept licenses for you.")
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args=p.parse_args();args.enable_cameras=True
    token=os.environ.get(args.token_env,"")
    if len(token)<16: raise SystemExit(f"Set {args.token_env} to a fresh random token (at least 16 characters)")
    from physical_exec.config import load_task
    task,limits=load_task(args.task)
    if args.allow_inspection_camera:
        from physical_exec.inspection_camera import camera_path
        view = task.get('extra_cameras', {}).get(task['camera_map']['right'])
        if view is None:
            raise ValueError('Inspection requires an explicitly configured initial right camera')
        # Reject incompatible static installations before starting an expensive GPU episode.
        camera_path(view['eye'], view['eye'], [0,0,0,1,0,0,0], [0,0,0,1,0,0,0],
                    1, 1/task['control_hz'], oblique_envelope=True)
    # Hardware capability is tested by Isaac itself. No CPU substitute is selected.
    launcher=AppLauncher(args);app=launcher.app
    server=None;env=None
    try:
        from physical_exec.backends.embodiedswe import EmbodiedSWEEnvironment
        from physical_exec.transport import make_server,EnvironmentService
        env=EmbodiedSWEEnvironment(args.repo,task,limits,device=args.device,record_dir=args.record_dir,
                                   record_depth=args.record_depth,allow_local_stages=args.allow_local_stages,
                                   local_stage_rotation_integral=args.local_stage_rotation_integral,
                                   allow_inspection_camera=args.allow_inspection_camera)
        env.worker_id=os.environ.get("PHYSICAL_EXEC_WORKER_ID") or __import__("uuid").uuid4().hex
        server=make_server(args.port,token,EnvironmentService(env).dispatch)
        print(f"READY simulator http://127.0.0.1:{server.server_port}; preset={task['preset']}; one episode only",flush=True)
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt: pass
    except Exception:
        # Isaac cleanup may block; preserve the original failure before entering it.
        traceback.print_exc()
        sys.stderr.flush()
        raise
    finally:
        if server: server.server_close()
        if env: env.close()
        app.close()

if __name__=="__main__": main()
