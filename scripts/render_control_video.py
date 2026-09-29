#!/usr/bin/env python3
"""Render genuine per-latch simulator frames; never invent frames or hide speed.

This is a subprocess wrapper around FFmpeg. No font files are packaged.
"""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording',type=Path,help='worker episode directory containing recording.json')
    p.add_argument('--view',default='left');p.add_argument('--speed',type=float,default=1)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
    a=p.parse_args();root=a.recording.resolve();meta=json.loads((root/'recording.json').read_text())
    if meta.get('frame_kind')!='every_control_latch' or meta.get('backend')!='embodiedswe':
        raise SystemExit('This renderer only accepts actual simulator per-control-latch recordings')
    if a.view not in meta['view_roles'] or not .1<=a.speed<=30: raise SystemExit('invalid view/speed')
    frames=sorted((root/a.view).glob('*.png'))
    if not frames or [x.name for x in frames] != [f'{i:06d}.png' for i in range(len(frames))]:
        raise SystemExit('Frames must be contiguous from 000000; no unreported frame omission')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.output.exists(): raise SystemExit('Refusing to overwrite video')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise SystemExit('Install ffmpeg first')
    label=f'SIMULATION | {a.speed:g}x simulated-time playback | model waits excluded'
    if meta.get('metadata',{}).get('grasp_weld') is True: label+=' | grasp assist ON'
    vf=f"setpts=PTS/{a.speed},drawtext=text='{label}':x=10:y=10:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.8,pad=ceil(iw/2)*2:ceil(ih/2)*2"
    cmd=[ffmpeg,'-n','-framerate',str(meta['fps']),'-i',str(root/a.view/'%06d.png'),'-vf',vf,
         '-r','30','-c:v','libx264','-pix_fmt','yuv420p',str(a.output)]
    print(__import__('shlex').join(cmd))
    if a.execute:
        subprocess.run(cmd,check=True)
        a.output.with_suffix('.json').write_text(json.dumps({'source':str(root),'frames':len(frames),
            'view':a.view,'speed':a.speed,'label':label,'time_model':meta['time_model']},indent=2)+'\n')
    else: print('Plan only; add --execute. Video excludes model waits, explicitly labelled.')

if __name__=='__main__': main()
