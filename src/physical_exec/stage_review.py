"""Single stage-boundary visual review; a recommendation never authorizes motion."""
import json


def review_messages(observation, outcome):
    content = [{"type": "text", "text": (
        "Review the current physical state and choose ONE next stage. This is a simulator-only "
        "PC graphics-card installation. The last operator-selected deeper grasp visibly tilted "
        "the card, but did not establish capture. Do not infer a grasp from gripper aperture. "
        "Do not continue forcing an obstructed lift. No object truth, force measurements, or "
        "collision certification is available. The hand frame is panda_hand, not contact center. "
        "Use only visible evidence and robot state. Available next stages: reopen_hold "
        "(open fingers while holding measured hand pose), inspect (no motion), or stop. "
        "Choose reopen_hold only if the visible support makes release reasonable; otherwise "
        "choose inspect or stop. No implicit retreat, regrasp, insertion or reset. "
        "Return JSON with stage, evidence, uncertainty, and next_visual_check, all strings. "
        "Keep each explanation under 100 words.\nRobot state: "
        + json.dumps(observation["state"]) + "\nLast execution: " + json.dumps(outcome))}]
    for role, image in observation["images"].items():
        content += [{"type": "text", "text": "Current camera: " + role},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image}}]
    return [{"role": "user", "content": content}]


def parse_review(content):
    value = json.loads(content)
    if set(value) != {"stage", "evidence", "uncertainty", "next_visual_check"}:
        raise ValueError("unexpected stage review fields")
    if value["stage"] not in {"reopen_hold", "inspect", "stop"}:
        raise ValueError("unsupported recovery stage")
    if any(not isinstance(v, str) or not v or len(v) > 2000 for v in value.values()):
        raise ValueError("invalid stage review text")
    return value
