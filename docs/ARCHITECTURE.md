# Architecture and contracts

```text
                         ORCHESTRATOR (core Python)
 actual sensor observation → memory → controller port → constrained Act tool
              ↑                              ↓
              │                   optional FLUX joint proposal
              │                   + robot-only FK preview
              │                              ↓
              └──── receipt + new view ← validated fresh command
                         │                       │
                         │                 loopback HTTP / SSH
                         │                       ↓
                    host-only grader     EMBODIEDSWE WORKER
                                         joint PD + DLS IK
                                              physics
                         FLUX WORKER (separate Python/Torch)
```

## Canonical representation

- Single Franka arm, explicit ordered seven joint names.
- SI units: meters, radians, seconds.
- EEF world pose: `[x,y,z,qw,qx,qy,qz]`, named frame `panda_hand`.
- Delta: `[dx,dy,dz,rx,ry,rz]`. Rotations left-multiply in world coordinates;
  each command builds on the preceding commanded pose in the chunk.
- Gripper: **open fraction**, 0 closed / 1 open. FLUX and EvalSim use closed fraction;
  convert exactly at those boundaries, not by changing the prompt.
- Each chunk has an observation ID, source, period, optional proposal ID, and bounded horizon.
- Unknown dimensions, stale IDs, invalid quaternions, wrong joint order and nonfinite values fail.
- Motion limits are rejection rules, not a proof of collision/contact safety.

## Policy observations

An `Observation` contains only task text, actual supplied images, robot joints/EEF/aperture,
step/time bookkeeping and conventions. Evaluator fields reside in an `Evaluation` object
handled by the orchestrator and audit log. The memory serializer never serializes raw
simulator dictionaries. Gripper closure is not a measured grasp-success signal.

There is no live object-coordinate RPC, scene graph, reward tool, reset tool, or shell tool
available to the model. The environment worker necessarily reads its native scorer, but
only for host termination/reporting. Reports can show it after the fact; requests cannot.

## Memory

The `LiveTrajectoryMemory` source file is exact RoboICL code. The wrapper saves:

1. the prior observation;
2. the model's public decision;
3. the **actual executed** command/prefix;
4. controller receipt, including tracking errors when available;
5. resulting observation.

Anchored selection does not imply constant token cost: retained records and images have
explicit byte/image caps, and large gap summaries can still grow. The wrapper checks caps
before sending a request. It does not silently truncate demonstrations or replace facts
with a summary. The optional summary hook labels its content unverified and references
observed evidence steps. It is not an implemented memory-optimization experiment.

Past successful traces can become reference blocks only after native success, trace/frame
verification, and matching robot/rate/EEF checks. Related tasks require explicit opt-in.
Old geometry is not automatically retargeted. No human-video imitation pipeline is included.

## Hybrid semantics

At each boundary FLUX generates a fresh joint chunk. The worker's robot-only URDF produces
its FK preview without advancing physics or inspecting objects. GPT can accept a prefix,
make a short constrained EEF correction, edit a preview, or stop incomplete. There is no
mode-switching scheduler or inferred confidence score.

The review gate rejects corrections motivated only by uncertainty. This follows the inspected
GPT-as-Policy gate. It may not be optimal for every task; preserve a reference before ablating it.

## Failure and reset semantics

- Pre-execution validation error: no physical step occurred; bounded model correction may retry.
- Model HTTP error: no model-selected action executes; no automatic inference retry/billing.
- Timeout or transport failure during a step: its outcome is ambiguous. Stop. Do not resend or reset.
- Repeated identical command ID: service returns its saved receipt without duplicate execution.
- Same ID with different content: reject.
- One environment reset per worker process. New episode requires a new worker.
- An external campaign watchdog can terminate a hung process; that attempt remains in the ledger.

## Evidence and timing

`events.jsonl` stores source-labelled proposals, public decisions, receipts, and host evaluation
separately. Frame hashes and linked event hashes detect inconsistency. `result.json` carries
wall time, simulated time, actual steps, decisions, usage and termination classification.

Reasoning tokens are a subset of output tokens, not an extra term. Cached input is a subset
of total input. Missing usage is explicitly flagged. The counter does not invent billable cost.

The HTML report contains observations at chunk boundaries. Native worker PNGs contain every
control latch. Neither is a real-time recording of model wait intervals. The FFmpeg tool labels
simulation, playback speed, excluded model waits, and enabled grasp-weld assistance.
