#!/usr/bin/env python3
"""Fetch exact audited upstream commits. Plan-only unless --execute is supplied.

No packages are installed, no checkpoints fetched, no licenses accepted, no
API calls made. Does not overwrite a dirty or differently pinned checkout.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def call(args,cwd=None,capture=False):
    return subprocess.run(args,cwd=cwd,check=True,text=True,capture_output=capture,
                          env={**os.environ,"GIT_LFS_SKIP_SMUDGE":"1"})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destination",type=Path,default=ROOT/"upstream")
    p.add_argument("--lock",type=Path,default=ROOT/"upstream.lock.json")
    p.add_argument("--only",nargs="*");p.add_argument("--execute",action="store_true")
    p.add_argument("--submodules",action="store_true",help="explicitly fetch pinned submodules too; may be large")
    p.add_argument("--verify-only",action="store_true")
    a=p.parse_args();lock=json.loads(a.lock.read_text())
    names={r['name'] for r in lock['repositories']}
    if a.only and set(a.only)-names: raise SystemExit(f"Unknown repository names: {set(a.only)-names}")
    for repo in lock['repositories']:
        if a.only and repo['name'] not in a.only: continue
        d=a.destination.resolve()/repo['name']
        print(f"{repo['name']} @ {repo['commit']} -> {d}",flush=True)
        if not a.execute and not a.verify_only: continue
        if not d.exists():
            if a.verify_only: raise SystemExit(f"Missing checkout {d}")
            d.mkdir(parents=True)
            call(['git','init',str(d)])
            call(['git','remote','add','origin',repo['url']],d)
            call(['git','fetch','--depth','1','origin',repo['commit']],d)
            call(['git','checkout','--detach',repo['commit']],d)
        else:
            sha=call(['git','rev-parse','HEAD'],d,True).stdout.strip()
            if sha != repo['commit']: raise SystemExit(f"Refusing to modify {d}: wrong commit {sha}")
            dirty=call(['git','status','--porcelain'],d,True).stdout.strip()
            if dirty: raise SystemExit(f"Refusing to certify dirty checkout {d}; preserve your work and use another directory")
        if a.submodules and not a.verify_only:
            call(['git','submodule','update','--init','--recursive'],d)
        for path,expected in repo.get('file_blobs',{}).items():
            actual=blob_sha((d/path).read_bytes())
            if actual!=expected: raise SystemExit(f"Audited file mismatch {repo['name']}/{path}: {actual}")
        print("  commit and audited files verified")
    if not a.execute and not a.verify_only: print("Plan only. Add --execute on a networked machine.")

if __name__=='__main__': main()
