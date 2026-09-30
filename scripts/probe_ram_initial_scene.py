#!/usr/bin/env python3
"""Host-local observation-only RAM probe with exact idle-FLUX restoration."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request


def request(port, token, path):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=b'{}',
                                 headers={'Authorization': 'Bearer '+token,
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def wait_ready(port, token, child=None):
    deadline = time.monotonic()+300
    while time.monotonic() < deadline:
        if child is not None and child.poll() is not None:
            raise RuntimeError('Worker exited before readiness; inspect log')
        try:
            return request(port, token, '/metadata')
        except (OSError, ValueError):
            time.sleep(2)
    raise RuntimeError('Worker readiness timeout; no reset retry')


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flux-pid', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8769)
    parser.add_argument('--retain-worker', action='store_true',
                        help='Keep successful fresh episode live; FLUX remains unloaded, private restart state saved')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    proc = Path('/proc')/str(args.flux_pid)
    command = proc.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
    if 'scripts/serve_flux.py' not in command:
        raise RuntimeError('Specified process is not the expected FLUX worker')
    env = dict(item.split('=', 1) for item in proc.joinpath('environ').read_bytes()
               .decode().rstrip('\0').split('\0'))
    cwd = proc.joinpath('cwd').resolve()
    for relative in ('scripts/serve_embodiedswe.py', 'scripts/capture_worker_observation.py',
                     'configs/tasks/pc_ram.json', 'upstream/EmbodiedSWE/.venv/bin/python'):
        if not (cwd/relative).is_file():
            raise RuntimeError('Missing probe prerequisite: '+relative)
    token = env['PHYSICAL_EXEC_FLUX_TOKEN']
    request(8766, token, '/metadata')
    connections = subprocess.check_output(['ss', '-Htn', 'state', 'established',
                                            'sport', '=', ':8766'], text=True)
    if connections.strip():
        raise RuntimeError('FLUX has an active connection; leave it untouched')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', args.port))
    sim_env = dict(item.split('=', 1) for item in Path('/proc/66502/environ')
                   .read_bytes().decode().rstrip('\0').split('\0'))
    # Preserve accepted runtime settings but isolate the new simulator to GPU1.
    sim_env['CUDA_VISIBLE_DEVICES'] = '1'
    sim_env['PHYSICAL_EXEC_SIM_TOKEN'] = Path('/tmp/physical_exec_sim_token').read_text().strip()
    python = 'upstream/EmbodiedSWE/.venv/bin/python'
    child = None
    stopped = False
    retained = False
    try:
        os.kill(args.flux_pid, signal.SIGTERM)
        stopped = True
        for _ in range(100):
            if not proc.exists() or ') Z ' in proc.joinpath('stat').read_text():
                break
            time.sleep(.2)
        else:
            stopped = False
            raise RuntimeError('FLUX did not exit; do not launch or duplicate it')
        with (args.output/'worker.log').open('w') as log:
            child = subprocess.Popen([python, '-u', 'scripts/serve_embodiedswe.py',
                '--repo', 'upstream/EmbodiedSWE', '--task', 'configs/tasks/pc_ram.json',
                '--record-dir', str(args.output/'recordings'), '--record-depth',
                '--allow-local-stages', '--local-stage-rotation-integral',
                '--port', str(args.port), '--headless'], cwd=cwd, env=sim_env,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        metadata = wait_ready(args.port, sim_env['PHYSICAL_EXEC_SIM_TOKEN'], child)
        (args.output/'metadata.json').write_text(json.dumps(metadata, indent=2))
        subprocess.run([python, 'scripts/capture_worker_observation.py', '--url',
            f'http://127.0.0.1:{args.port}', '--reset', '--output', str(args.output/'capture')],
            cwd=cwd, env=sim_env, check=True, timeout=180)
        print('RAM initial capture complete; no control actions issued', flush=True)
        if args.retain_worker:
            # The exact environment can contain tokens: keep it outside artifacts, mode0600.
            fd, filename = tempfile.mkstemp(prefix='physical_exec_flux_restore_', suffix='.json')
            with os.fdopen(fd, 'w') as stream:
                json.dump({'command': command, 'cwd': str(cwd), 'env': env}, stream)
            (args.output/'retained_worker.json').write_text(json.dumps({
                'ram_pid': child.pid, 'port': args.port, 'flux_unloaded': True,
                'private_flux_restore_path': filename, 'ram_control_actions': 0}))
            retained = True
            print('RAM retained: '+str(child.pid)+'; FLUX intentionally unloaded', flush=True)
    finally:
        if not retained and child is not None and child.poll() is None:
            child.send_signal(signal.SIGINT)
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=30)
        if stopped and not retained:
            with (args.output/'flux_restore.log').open('w') as log:
                restored = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            wait_ready(8766, token, restored)
            (args.output/'restoration.json').write_text(json.dumps({
                'flux_pid': restored.pid, 'ready': True, 'ram_control_actions': 0}))
            print('FLUX restored and authenticated ready: '+str(restored.pid), flush=True)


if __name__ == '__main__':
    main()
