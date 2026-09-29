"""Authenticated loopback JSON/PNG transport. No pickle or arbitrary RPC methods.

The simulator is deliberately a separate process/interpreter from the model.
There are no automatic retries for state-changing requests.
"""
from __future__ import annotations
from dataclasses import asdict
import base64
from io import BytesIO
import json
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import urlsplit
import numpy as np
import httpx
from PIL import Image
from .contracts import Observation, ActionChunk, ExecutionReceipt, StepResult, Evaluation
from .errors import InputRejected, AmbiguousExecution, ProtocolError
from .imaging import png_bytes
from .trace import dumps

MAX_MESSAGE = 40_000_000


def encode_observation(obs: Observation) -> dict:
    return {"state": obs.public_state(), "images": {k: base64.b64encode(png_bytes(v)).decode("ascii") for k,v in obs.images.items()}}


def decode_observation(data: dict) -> Observation:
    if set(data) != {"state", "images"}: raise ProtocolError("invalid observation envelope")
    s = data["state"]; images = {}
    allowed = {"observation_id", "episode_id", "step", "sim_time_seconds", "task", "robot", "joints_rad", "joint_names",
               "eef_pose_world_xyz_wxyz", "eef_frame", "gripper_open_fraction", "gripper_state_source", "control_dt_seconds", "camera_roles"}
    if set(s) != allowed: raise ProtocolError("unknown or missing policy-state field")
    if len(data["images"]) > 8: raise ProtocolError("too many cameras")
    for role, value in data["images"].items():
        if not isinstance(value, str) or len(value) > MAX_MESSAGE: raise ProtocolError("oversized image")
        b = base64.b64decode(value, validate=True)
        with Image.open(BytesIO(b)) as im:
            if im.format != "PNG" or max(im.size) > 4096: raise ProtocolError("invalid image format/size")
            images[role] = np.asarray(im.convert("RGB")).copy()
    if set(images) != set(s["camera_roles"]) or len(s["camera_roles"]) != len(images):
        raise ProtocolError("camera role mismatch")
    images = {role: images[role] for role in s["camera_roles"]}
    obs = Observation(s["episode_id"], s["step"], s["sim_time_seconds"], s["task"], s["robot"], images,
                      np.array(s["joints_rad"]), tuple(s["joint_names"]), np.array(s["eef_pose_world_xyz_wxyz"]),
                      s["gripper_open_fraction"], s["control_dt_seconds"], s["eef_frame"])
    if obs.key != s["observation_id"]: raise ProtocolError("observation identity mismatch")
    return obs


def encode_result(result: StepResult) -> dict:
    return {"observation": encode_observation(result.observation), "receipt": result.receipt.to_dict(),
            "evaluation_host_only": asdict(result.evaluation)}


def decode_result(obj: dict) -> StepResult:
    if set(obj) != {"observation", "receipt", "evaluation_host_only"}: raise ProtocolError("invalid step result")
    return StepResult(decode_observation(obj["observation"]), ExecutionReceipt(**obj["receipt"]),
                      Evaluation(**obj["evaluation_host_only"]))


class LocalClient:
    def __init__(self, url: str, token: str, timeout: float = 120, client=None):
        u = urlsplit(url)
        if u.scheme != "http" or u.hostname not in {"127.0.0.1", "localhost", "::1"} or u.username or u.password or u.query or u.fragment:
            raise ValueError("worker URLs must use loopback HTTP; use an SSH tunnel for remote workers")
        if not token or len(token) < 16: raise ValueError("worker token must have at least 16 characters")
        self.url, self.token, self.timeout = url.rstrip("/"), token, timeout
        self.client = client or httpx.Client(follow_redirects=False, trust_env=False)
        self.owns = client is None

    def call(self, path: str, payload: dict | None = None, mutating: bool = False) -> dict:
        try:
            response = self.client.post(self.url+path, content=dumps(payload or {}).encode(),
                                        headers={"Authorization": "Bearer "+self.token,
                                                 "Content-Type": "application/json"}, timeout=self.timeout)
        except httpx.HTTPError as e:
            cls = AmbiguousExecution if mutating else ProtocolError
            raise cls(f"worker transport error ({type(e).__name__}); do not retry execution/reset") from e
        if len(response.content) > MAX_MESSAGE: raise ProtocolError("oversized worker reply")
        try: result = response.json()
        except ValueError as e:
            cls = AmbiguousExecution if mutating else ProtocolError
            raise cls("non-JSON worker reply") from e
        if response.status_code == 422 and result.get("no_execution") is True:
            raise InputRejected(str(result.get("error", "input rejected")))
        if response.status_code != 200:
            cls = AmbiguousExecution if mutating else ProtocolError
            raise cls(f"worker HTTP {response.status_code}: {result.get('error', 'unknown error')}")
        return result

    def close(self):
        if self.owns: self.client.close()
        self.token = ""


def make_server(port: int, token: str, dispatch: Callable[[str, dict], dict]) -> HTTPServer:
    if len(token) < 16: raise ValueError("worker auth token required")
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer "+token):
                self._reply(401, {"error": "unauthorized"}); return
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if not 0 < n <= MAX_MESSAGE: raise ValueError("invalid body size")
                self.connection.settimeout(30)
                raw = self.rfile.read(n)
                if len(raw) != n: raise ValueError("truncated body")
                data = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                if not isinstance(data, dict): raise ValueError("expected JSON object")
            except (ValueError, TimeoutError) as e:
                self._reply(400, {"error": type(e).__name__, "no_execution": True}); return
            try:
                result = dispatch(self.path, data)
                self._reply(200, result)
            except InputRejected as e:
                self._reply(422, {"error": str(e)[:2000], "no_execution": True})
            except Exception as e:
                # Do NOT describe arbitrary partial failures as safe for retry.
                self._reply(500, {"error": type(e).__name__+": "+str(e)[:2000], "no_execution": False})
        def _reply(self, status, body):
            data = dumps(body).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers()
            try: self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError): pass
        def log_message(self, *args): pass  # do not log authorization or observation payloads
    return HTTPServer(("127.0.0.1", port), Handler)


class EnvironmentService:
    def __init__(self, env):
        self.env = env; self.observation = None; self.poisoned = False; self.reset_attempted = False
        self.commands: dict[str, tuple[str, dict]] = {}

    def dispatch(self, path: str, payload: dict) -> dict:
        if path == "/metadata": return self.env.metadata()
        if path == "/reset":
            if self.reset_attempted: raise InputRejected("one episode per worker; restart it for another run")
            if set(payload) != {"seed"} or type(payload["seed"]) is not int: raise InputRejected("invalid seed")
            self.reset_attempted = True
            self.observation = self.env.reset(payload["seed"])
            return encode_observation(self.observation)
        if path == "/evaluate": return asdict(self.env.evaluate())
        if path == "/observe":
            if self.observation is None: raise InputRejected("reset first")
            return encode_observation(self.observation)
        if path in ("/step", "/local-stage"):
            if self.observation is None: raise InputRejected("reset first")
            if self.poisoned: raise AmbiguousExecution("worker halted after ambiguous execution")
            if set(payload) != {"command_id", "action"}: raise InputRejected("invalid step envelope")
            cid = payload["command_id"]
            if not isinstance(cid, str) or not 1 <= len(cid) <= 100: raise InputRejected("invalid command id")
            fingerprint = dumps({'path': path, 'payload': payload})
            if cid in self.commands:
                old, reply = self.commands[cid]
                if old != fingerprint: raise InputRejected("command ID reuse with different arguments")
                return reply
            if path == '/step':
                try: action = ActionChunk.from_dict(payload["action"])
                except (TypeError, ValueError) as e: raise InputRejected(str(e)) from e
            elif not getattr(self.env, 'allow_local_stages', False):
                raise InputRejected('local stages not enabled')
            try:
                result = (self.env.step(action, cid) if path == '/step'
                          else self.env.local_stage(payload['action'], cid))
            except InputRejected: raise
            except Exception:
                self.poisoned = True; raise
            reply = encode_result(result)
            self.commands[cid] = (fingerprint, reply); self.observation = result.observation
            return reply
        if path == "/fk":
            if self.observation is None: raise InputRejected("reset first")
            if set(payload) != {"observation_id", "joints", "joint_names"}: raise InputRejected("invalid FK envelope")
            if payload["observation_id"] != self.observation.key: raise InputRejected("stale FK request")
            if not hasattr(self.env, "fk_preview"): raise InputRejected("backend has no FK service")
            return {"poses": self.env.fk_preview(np.asarray(payload["joints"]), tuple(payload["joint_names"])).tolist()}
        raise InputRejected("unknown RPC; no general simulator/code/state-access method exists")


class RemoteEnvironment:
    def __init__(self, client: LocalClient):
        self.client = client; self._evaluation = Evaluation()
        self._metadata = client.call("/metadata")
    def reset(self, seed): return decode_observation(self.client.call("/reset", {"seed": seed}, mutating=True))
    def observe(self): return decode_observation(self.client.call("/observe"))
    def step(self, action, command_id):
        result = decode_result(self.client.call("/step", {"command_id": command_id, "action": action.to_dict()}, mutating=True))
        self._evaluation = result.evaluation
        return result
    def evaluate(self): return Evaluation(**self.client.call("/evaluate"))
    def metadata(self): return self._metadata.copy()
    def fk_preview(self, obs: Observation, joints):
        return np.asarray(self.client.call("/fk", {"observation_id": obs.key, "joints": np.asarray(joints).tolist(),
                                                   "joint_names": list(obs.joint_names)})["poses"])
    def close(self): self.client.close()
