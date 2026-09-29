"""Offline reports only. Never query models or relabel fixture output as success."""
from __future__ import annotations
import base64
import csv
import html
import json
from pathlib import Path
from .trace import verify_trace, write_json


def load_run(root):
    root = Path(root).resolve(); verify_trace(root)
    manifest = json.loads((root/"manifest.json").read_text())
    result = json.loads((root/"result.json").read_text())
    events = [json.loads(x) for x in (root/"events.jsonl").read_text().splitlines()]
    return root, manifest, result, events


def render_html(root, destination=None):
    root, m, result, events = load_run(root)
    dest = Path(destination) if destination else root/"report.html"
    esc = html.escape
    fixture = m.get("backend") == "fixture"
    heading = "SOFTWARE FIXTURE — NO ROBOT OR MODEL RESULT" if fixture else "SIMULATION EXPERIMENT — NOT REAL-WORLD VALIDATION"
    summary = {"task": m.get("task_instruction"), "controller": m.get("controller_mode"),
               "reasoning": m.get("reasoning_effort"), "native_success": result.get("native_success"),
               "termination": result.get("terminal_reason"), "wall_seconds": result.get("wall_seconds"),
               "simulated_seconds": result.get("simulated_seconds"), "usage": result.get("usage"),
               "physics_assists": m.get("physics_assists"), "grasp_weld": m.get("grasp_weld"),
               "time_model": m.get("time_model")}
    blocks = []
    for event in events:
        k, d = event["kind"], event["data"]
        if k == "observation":
            imgs = []
            for role in d["camera_roles"]:
                path = (root/d["images"][role]["path"]).resolve()
                if not path.is_relative_to(root): raise ValueError("path escapes run")
                url = "data:image/png;base64,"+base64.b64encode(path.read_bytes()).decode()
                imgs.append(f'<figure><img src="{url}" alt="{esc(role)}"><figcaption>{esc(role)}</figcaption></figure>')
            blocks.append(f'<section><h2>Observation {d["step"]}</h2><div class="images">'+"".join(imgs)+"</div></section>")
        elif k in ("decision", "execution_receipt", "input_rejected_no_execution", "run_finished", "host_prefix_limit"):
            if k == "decision": d = {"public_decision": d["public_decision"], "usage": d.get("usage")}
            blocks.append(f'<details open><summary>{esc(k)}</summary><pre>{esc(json.dumps(d,indent=2))}</pre></details>')
    doc = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adaptive physical execution — run evidence</title><style>
body{{font:16px system-ui,sans-serif;max-width:1160px;margin:32px auto;padding:0 20px;background:#10151d;color:#e6edf5}}
h1{{font-size:24px}}.banner{{padding:18px;border:2px solid #edb56e}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#182230;padding:16px}}
.images{{display:flex;gap:12px;flex-wrap:wrap}}figure{{margin:0;flex:1;min-width:220px}}img{{width:100%;height:auto}}details{{margin:16px 0}}section{{margin:30px 0}}figcaption{{padding:8px}}
</style><h1>{esc(heading)}</h1><p class="banner">Boundary observations, not a continuous rollout movie. Full model waiting time is included in wall time, not in simulated time. Public assessments are model reports, not measured object truth. No hidden reasoning is displayed.</p>
<pre>{esc(json.dumps(summary,indent=2))}</pre>{''.join(blocks)}</html>'''
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(doc)
    return dest


def compare_runs(roots, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    rows=[]
    for path in roots:
        root,m,r,_=load_run(path)
        u=r.get("usage",{})
        rows.append({"run":str(root),"task":m.get("preset",m.get("task_instruction")),
                     "backend":m.get("backend"),"controller":m.get("controller_mode"),
                     "reasoning_effort":m.get("reasoning_effort"),"seed":m.get("seed"),
                     "native_success":r.get("native_success"),"fixture_pass":r.get("fixture_pass"),
                     "terminal_reason":r.get("terminal_reason"),"wall_seconds":r.get("wall_seconds"),
                     "simulated_seconds":r.get("simulated_seconds"),"decision_count":r.get("decision_count"),
                     "gpt_calls":u.get("provider_attempts"),"input_tokens":u.get("input_tokens"),
                     "cached_input_tokens":u.get("cached_input_tokens"),"output_tokens":u.get("output_tokens"),
                     "all_usage_reported":u.get("all_usage_reported"),"grasp_weld":m.get("grasp_weld")})
    write_json(output/"runs.json", {"runs":rows,"scope":"Descriptive only. No cross-task aggregate or statistical improvement claim."})
    if rows:
        with (output/"runs.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return output
