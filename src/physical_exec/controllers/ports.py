"""Two explicit single-arm controller ports and a hybrid composition.

Not benchmark-equivalent upstream reproductions: camera layout, single-arm
schema, API transport and downstream IK differ. Native launchers are supplied
separately. The anchor-selection implementation itself is verbatim RoboICL.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
import numpy as np
from ..contracts import ActionChunk, Observation, Usage
from ..errors import InputRejected
from ..geometry import quat_mul, rotvec_to_quat, unit_quaternion, pose_matrix
from ..memory import ExecutionMemory, user_text, enforce_context_budget
from ..providers.responses import ModelReply
from ..safety import Limits
from ..trace import dumps


def obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def vector(n: int) -> dict:
    return {"type": "array", "items": {"type": "number"}, "minItems": n, "maxItems": n}


ASSESSMENT = obj({"execution_status": {"type": "string", "enum": ["not_started", "progressing", "failed", "uncertain", "recovered"]},
                  "intent_status": {"type": "string", "enum": ["aligned", "misaligned", "uncertain"]},
                  "evidence": {"type": "string"}})


def direct_schema(mode: str, horizon: int) -> dict:
    step = obj({"delta_world": vector(6), "gripper_open": {"type": "number"}}) if mode == "direct_roboicl" else obj({"pose_world_xyz_wxyz": vector(7), "gripper_open": {"type": "number"}})
    return obj({"observation_id": {"type": "string"}, "intent": {"type": "string"},
                "assessment": ASSESSMENT,
                "actions": {"type": "array", "items": step, "minItems": 1, "maxItems": horizon}})


def hybrid_schema(horizon: int) -> dict:
    return obj({"observation_id": {"type": "string"}, "proposal_id": {"type": "string"},
                "mode": {"type": "string", "enum": ["accept", "edit", "eef", "stop"]},
                "execute_steps": {"type": "integer", "minimum": 0, "maximum": horizon},
                "assessment": ASSESSMENT, "reason": {"type": "string"},
                "translation_world": vector(3), "rotation_world": vector(3),
                "gripper_override": {"type": "string", "enum": ["keep", "open", "closed"]},
                "actions": {"type": "array", "minItems": 0, "maxItems": 5,
                            "items": obj({"pose_world_xyz_wxyz": vector(7), "gripper_open": {"type": "number"}})}})


def validate_schema(value, schema: dict, path="decision"):
    """Small strict validator for the schemas above; avoids another runtime dependency."""
    typ = schema.get("type")
    if typ == "object":
        if not isinstance(value, dict): raise InputRejected(f"{path} must be an object")
        if set(value) != set(schema["required"]):
            raise InputRejected(f"{path} requires exactly {schema['required']}")
        for k, s in schema["properties"].items(): validate_schema(value[k], s, path+"."+k)
    elif typ == "array":
        if not isinstance(value, list) or not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100000):
            raise InputRejected(f"{path}: invalid array length/type")
        for v in value: validate_schema(v, schema["items"], path+"[]")
    elif typ == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise InputRejected(f"{path}: expected finite number, not bool")
    elif typ == "integer":
        if type(value) is not int: raise InputRejected(f"{path}: expected integer")
    elif typ == "string":
        if not isinstance(value, str) or len(value) > 10000: raise InputRejected(f"{path}: invalid string")
    if "enum" in schema and value not in schema["enum"]: raise InputRejected(f"{path}: invalid enum")
    if "minimum" in schema and value < schema["minimum"]: raise InputRejected(f"{path}: below minimum")
    if "maximum" in schema and value > schema["maximum"]: raise InputRejected(f"{path}: above maximum")


BASE_PROMPT = """You control ONE robot arm in a simulation via the Act tool. There is no shell,
scene-object lookup, reward query, reset, or arbitrary-code tool. The task instruction stays
fixed while the observed physical state can change. Use only supplied RGB, robot proprioception,
robot kinematics and actual execution receipts. Distinguish a proposed/commanded action from what
actually happened. Gripper closure alone does not verify a grasp. You may infer object state from
images but state uncertainty; never assert hidden poses/contact forces. Retained memory can contain
gaps; do not assume task success across them. Prior demonstrations use old geometry: adapt to the
current scene. Public assessment should be short and evidence-based, not a private reasoning trace.
Quaternions are w,x,y,z. Translations are meters and rotation vectors radians. Canonical gripper
commands are OPEN fraction: 0=closed, 1=open. EEF poses describe the named robot frame, not an
assumed contact point. Observe slips and recover from the current state without rewriting a program.
"""


HYBRID_GATE = """Assess LAST execution separately from NEXT policy intent. Compare before/after
RGB and measured robot state; update subgoal completion only from visible evidence and undo it
if later observations contradict it. Infer proposal intent from ROBOT-ONLY FK and gripper targets;
there is no predicted object future. Allow the student to self-correct. An edit/EEF takeover requires
execution_status='failed' OR intent_status='misaligned'. Uncertainty alone does not authorize takeover.
Keep the original task as the student's input. 'accept' executes a prefix of the fresh proposal;
'edit' shifts/rotates its EEF targets and optionally changes the gripper; 'eef' supplies short bounded
absolute EEF targets. 'stop' ends incomplete, never claims success. Review EVERY proposal in this
initial implementation; sparse/event-triggered invocation is NOT enabled.
Robot motion alone is not task progress. For an approach, cite visible reduction in
hand-to-target separation or improved grasp alignment across views; a downward move
by itself is insufficient. If that cannot be established, use execution_status='uncertain'.
For repeated proposals that move away from the visible target, mark intent misaligned
and stop or correct within the existing rules. Uncertainty during an open-gripper
approach is not itself failure and has no fixed chunk-count stopping rule. Allow
bounded self-correction within the run budget when the next motion is reasonable;
stop for concerning motion or repeated observable lack of progress. Do not continue
closed-gripper transport merely on an unverified grasp assumption.
"""


@dataclass(frozen=True)
class Proposal:
    action: ActionChunk
    eef_preview: np.ndarray  # Hx8 xyz+wxyz+open; robot-only FK
    model_identity: str
    inference_seconds: float
    boundary_conversion: dict | None = None

    def public(self) -> dict:
        return {"proposal_id": self.action.proposal_id, "observation_id": self.action.observation_id,
                "boundary_conversion": self.boundary_conversion,
                "model_identity": self.model_identity,
                "joint_proposal": self.action.to_dict(),
                "robot_only_fk_world_xyz_wxyz_gripper_open": self.eef_preview.tolist(),
                "notice": "FK of the robot only; no object states, contacts, rewards or simulated object futures."}


class ProposalSource(Protocol):
    def propose(self, observation: Observation) -> Proposal: ...


@dataclass(frozen=True)
class ControllerDecision:
    action: ActionChunk | None
    raw: dict
    usage: Usage
    response_id: str
    proposal: Proposal | None = None
    depth_samples: list | None = None


class ControllerPort:
    def __init__(self, mode: str, provider, memory: ExecutionMemory,
                 limits: Limits, horizon: int = 5, proposer: ProposalSource | None = None):
        if mode not in ("direct_roboicl", "direct_reference", "hybrid"):
            raise ValueError("unknown controller mode")
        if not 1 <= horizon <= 32: raise ValueError("invalid horizon")
        if mode == "direct_reference" and horizon > 5:
            raise ValueError("Direct reference port retains the 1..5-step interface")
        if mode == "hybrid" and proposer is None: raise ValueError("hybrid requires a proposer")
        self.mode, self.provider, self.memory = mode, provider, memory
        self.limits, self.horizon, self.proposer = limits, horizon, proposer
        self.last_reply: ModelReply | None = None
        self.last_proposal = None

    def decide(self, observation: Observation, timeout_seconds=None) -> ControllerDecision:
        self.last_reply = None; self.last_proposal = None
        messages = self.memory.render(observation)
        prompt = BASE_PROMPT + ("\n" + HYBRID_GATE if self.mode == "hybrid" else "")
        if getattr(self, 'local_eef_execution', False):
            prompt += ('\nENHANCED EEF EXECUTION: supply exactly one EEF target per decision. '
                'It is a bounded destination, not a single control-tick command: local feedback '
                'may execute up to64 actions before returning a fresh observation/receipt. '
                'Do not send a multi-target EEF sequence. Native joint proposals retain their '
                'original timing. A local tracking stop or nonarrival ends this run without retry.')
            if getattr(self,'fast_open_transit',False):
                prompt += (' Elevated open-hand destinations use experimental smooth5x transit when both '
                    'hand endpoint heights are at least0.30m; other destinations use conservative motion. '
                    'This geometric scope rule does NOT establish obstacle clearance. Choose targets '
                    'from current evidence, not merely to qualify for the fast profile.')
        if observation.robot == 'franka' and observation.eef_frame == 'panda_hand':
            # Pinned EmbodiedSWE robot pad-center convention, also used by its RL tasks.
            pinch = (pose_matrix(observation.eef_pose) @ np.array([0., 0., .1034, 1.]))[:3]
            prompt += ("\nRobot geometry: the nominal finger-pad pinch center is [0,0,0.1034] m"
                       " in panda_hand coordinates, along hand-local +z, NOT world +z."
                       " Current nominal pinch center world XYZ is " + dumps(pinch.tolist()) +
                       ". This is computed from robot proprioception, not an object pose or contact measurement."
                       " Hand-frame arrival, wrist-image proximity, and finger closure do not establish pad contact."
                       " Use external views to assess whether the pads actually straddle the target before interpreting a lift test.")
        prompt += f"\nFor EEF commands: per-step Euclidean translation limit {self.limits.max_translation_m} m; rotation limit {self.limits.max_rotation_rad} rad."
        if self.mode == "hybrid":
            prompt += (f" Joint proposals instead have a per-joint target-step limit of {self.limits.max_joint_step_rad} rad."
                       " Their FK previews are not EEF commands: do not call an FK displacement a violation of the EEF command limit."
                       " You may still stop for concerning motion, poor alignment, or inadequate evidence; explain that as a review judgment.")
        if self.mode == "hybrid":
            proposal = self.proposer.propose(observation)
            self.last_proposal = proposal
            if proposal.action.observation_id != observation.key or not proposal.action.proposal_id:
                raise InputRejected("proposer returned stale/unidentified chunk")
            messages.append(user_text("<FRESH_POLICY_PROPOSAL>" + dumps(proposal.public()) + "</FRESH_POLICY_PROPOSAL>"))
            schema = hybrid_schema(min(self.horizon, len(proposal.action.values)))
            prompt += " Unused edit vectors must be [0,0,0]; unused actions must be []."
        else:
            proposal = None
            schema = direct_schema(self.mode, self.horizon)
            if self.mode == "direct_roboicl":
                prompt += ("\nGenerate 1..%d per-step world-frame Cartesian increments. Translation adds in world; rotation left-multiplies the previous target. Each next row builds on the previous commanded row, not the initial pose." % self.horizon)
            else:
                prompt += "\nGenerate 1..5 absolute EEF world-pose targets; use short observed-state corrections."
        if getattr(self, 'depth_queries', False):
            if self.mode == 'hybrid':
                raise ValueError('depth queries currently require Direct mode')
            schema['properties']['actions']['minItems'] = 0
            schema['properties']['decision_type'] = {'type':'string','enum':['act','measure_depth']}
            schema['properties']['samples'] = {'type':'array','minItems':0,'maxItems':6,
                'items':obj({'camera':{'type':'string','enum':list(observation.images)},
                             'pixel_uv':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'integer'}}})}
            schema['required'] += ['decision_type','samples']
            prompt += ('\nDEPTH QUERY: choose decision_type=measure_depth with 1..6 visible solid '
                'pixels in samples and actions=[] to receive measured world/hand coordinates '
                'without motion. Pixel coordinates are original image integer [u,v], upper-left origin. '
                'Each query consumes a decision/call. For decision_type=act use samples=[] and '
                'nonempty actions. A surface sample is not object center, hidden thickness or clearance. '
                'Use measured offsets before uncertain contact positioning; never copy a face offset '
                'as a grasp-center correction. Query results are valid only for the current observation.')
            feedback = getattr(self,'depth_feedback',None)
            if feedback is not None and feedback['observation_id'] == observation.key:
                messages.append(user_text('CURRENT SENSOR DEPTH MEASUREMENTS: '+dumps(feedback)))
        enforce_context_budget(messages, self.memory.config)
        reply = self.provider.act(prompt, messages, schema, timeout_seconds=timeout_seconds)
        self.last_reply = reply
        validate_schema(reply.arguments, schema)
        raw = reply.arguments
        if raw["observation_id"] != observation.key:
            raise InputRejected("model selected an old observation")
        if getattr(self,'depth_queries',False):
            if raw['decision_type']=='measure_depth':
                if raw['actions'] or not raw['samples']:
                    raise InputRejected('depth query requires samples and no actions')
                return ControllerDecision(None,raw,reply.usage,reply.response_id,depth_samples=raw['samples'])
            if raw['samples'] or not raw['actions']:
                raise InputRejected('act requires actions and no depth samples')
        try:
            if self.mode == "hybrid":
                action = self._hybrid_action(raw, observation, proposal)
            else:
                key = "delta_world" if self.mode == "direct_roboicl" else "pose_world_xyz_wxyz"
                a = [x[key] + [x["gripper_open"]] for x in raw["actions"]]
                kind = "eef_delta_world" if self.mode == "direct_roboicl" else "eef_absolute_world"
                action = ActionChunk(kind, np.asarray(a), observation.key, observation.control_dt, self.mode)
        except ValueError as e:
            raise InputRejected(str(e)) from e
        return ControllerDecision(action, raw, reply.usage, reply.response_id, proposal)

    def _hybrid_action(self, raw: dict, obs: Observation, p: Proposal):
        if raw["proposal_id"] != p.action.proposal_id: raise InputRejected("stale proposal id")
        mode, n = raw["mode"], raw["execute_steps"]
        if mode == "stop":
            if n != 0: raise InputRejected("stop must execute zero steps")
            return None
        if n < 1 or n > len(p.action.values): raise InputRejected("invalid requested prefix")
        if mode in ("edit", "eef"):
            a = raw["assessment"]
            if a["execution_status"] != "failed" and a["intent_status"] != "misaligned":
                raise InputRejected("gate disallows takeover for uncertainty alone")
            if n > 5: raise InputRejected("corrections limited to five steps")
        if mode == "accept":
            if raw["actions"] or any(raw["translation_world"]) or any(raw["rotation_world"]) or raw["gripper_override"] != "keep":
                raise InputRejected("accept may not hide edits")
            return p.action.prefix(n)
        if mode == "eef":
            if any(raw["translation_world"]) or any(raw["rotation_world"]) or raw["gripper_override"] != "keep":
                raise InputRejected("EEF mode may not hide extra edits")
            if len(raw["actions"]) != n: raise InputRejected("EEF correction length mismatch")
            rows = [x["pose_world_xyz_wxyz"]+[x["gripper_open"]] for x in raw["actions"]]
        else:
            if raw["actions"]: raise InputRejected("edit mode uses FK proposal, not alternative actions")
            d, r = np.array(raw["translation_world"]), np.array(raw["rotation_world"])
            if np.linalg.norm(d) > .05 or np.linalg.norm(r) > .35:
                raise InputRejected("edit exceeds published-style correction bound")
            rows = np.array(p.eef_preview[:n], copy=True)
            rows[:, :3] += d
            for row in rows: row[3:7] = unit_quaternion(quat_mul(rotvec_to_quat(r), row[3:7]))
            if raw["gripper_override"] != "keep":
                rows[:, -1] = 1.0 if raw["gripper_override"] == "open" else 0.0
        return ActionChunk("eef_absolute_world", np.array(rows), obs.key, obs.control_dt,
                           "gpt_hybrid_"+mode, proposal_id=p.action.proposal_id)
