#!/usr/bin/env python3
"""Make an operator-routed native RoboICL profile without editing the upstream.

The published profile contains a third-party gateway/model alias. Those are NOT
safe defaults for your key. Output is a new profile with your explicit values.
"""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from physical_exec.providers.responses import ProviderConfig

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--endpoint',required=True);p.add_argument('--model',required=True)
    p.add_argument('--reasoning',choices=['medium','high','xhigh'],default='medium')
    p.add_argument('--shots',type=int,choices=[0,1],default=0);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();ProviderConfig(a.model,a.endpoint,reasoning_effort=a.reasoning)
    native='zero_shot_b25.json' if a.shots==0 else 'one_shot_j12_b12.json'
    profile=json.loads((a.repo/'configs/protocols'/native).read_text())
    profile['id']='operator-'+profile['id'];profile['model']=a.model;profile['endpoint']=a.endpoint
    profile['harness_overrides']['reasoning_effort']=a.reasoning
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f: json.dump(profile,f,indent=2);f.write('\n')
    print(f"Wrote {a.output}. No API call made. Run upstream --dry-run, then --capture-only before a rollout.")

if __name__=='__main__': main()
