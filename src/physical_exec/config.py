"""Small JSON configurations; no executable YAML or implicit environment discovery."""
from __future__ import annotations
from pathlib import Path
import json
from .safety import Limits

TASKS = {"pc_gpu", "pc_ram", "pc_gpu_ram", "bulb"}

def read_json(path):
    p = Path(path)
    if p.stat().st_size > 2_000_000: raise ValueError("configuration too large")
    obj = json.loads(p.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if not isinstance(obj, dict): raise ValueError("configuration must be a JSON object")
    return obj


def load_task(path):
    obj = read_json(path)
    allowed = {"schema", "id", "preset", "instruction", "control_hz", "image_size", "camera_map",
               "extra_cameras", "limits", "default_horizons", "notes", "source", "wrist_target_hand"}
    if set(obj)-allowed: raise ValueError(f"unknown task fields: {set(obj)-allowed}")
    if obj.get("schema") != "physical-exec-task/v1" or obj.get("id") not in TASKS:
        raise ValueError("unknown task/schema")
    if obj.get("preset") != f"assembly.{obj['id']}.franka.joint":
        raise ValueError("initial release supports explicit single-Franka joint presets only")
    if not isinstance(obj.get("instruction"), str) or not obj["instruction"].strip():
        raise ValueError("supply a literal task instruction")
    if not 1 <= obj.get("control_hz", 0) <= 100: raise ValueError("invalid control frequency")
    cams = obj.get("camera_map", {})
    if set(cams) != {"wrist", "left", "right"} or len(set(cams.values())) != 3:
        raise ValueError("declare three distinct cameras")
    size = obj.get("image_size", [])
    if len(size) != 2 or any(type(x) is not int or not 32 <= x <= 4096 for x in size):
        raise ValueError("image_size is [width,height]")
    if 'wrist_target_hand' in obj:
        from .geometry import finite_vector
        import numpy as np
        target = finite_vector(obj['wrist_target_hand'], 3)
        if np.linalg.norm(target) > .4 or np.linalg.norm(target-[.0465,-.02,.036]) < .01:
            raise ValueError('invalid robot-local wrist target')
    limits = Limits(**obj.get("limits", {}))
    return obj, limits


def configured_camera_view(task, name, view):
    """Opt-in wrist aim, leaving default camera installation and input unchanged."""
    if 'wrist_target_hand' not in task or name != task['camera_map']['wrist']:
        return view
    if view.get('link') != 'panda_hand':
        raise ValueError('wrist target requires the pinned Panda hand frame')
    return {**view, 'target':list(task['wrist_target_hand'])}
