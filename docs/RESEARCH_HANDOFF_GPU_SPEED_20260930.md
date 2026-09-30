# Research Handoff: GPU-First Execution and Motion-Speed Results

Date: September 30, 2026 (JST). Repository: https://github.com/AranKomat/adaptive-physical-execution

Experiment/code snapshot: `18c0ea9`. This document supersedes older live-state
summaries and covers progress since the previous broad project handoff, with
enough background to read independently. It describes simulator experiments,
not real-hardware deployment or a completed robotics benchmark.

## Executive Summary

The user has redirected work to **GPU installation**, suspending RAM experiments.
The priority is reliable, substantially faster manipulation, then a matched
comparison of enhanced GPT Direct-A, Direct-B, and FLUX+GPT Hybrid.

The latest useful result is a **5x-speed-cap, feedforward-assisted local EEF
controller completing an unloaded 12 cm up-and-return motion in 4.53 simulated
seconds**, versus 13.93 seconds for the conservative controller test. Endpoint
errors were 0.336 mm and 0.216 mm; no tracking guard stopped this run.

This is **3.07x faster total simulated execution**, not a 5x measured task speedup.
The 5x label describes peak trajectory-speed limits. Acceleration, braking and
settling matter. A subsequent 10x attempt exceeded the unchanged tracking guard
and stopped. No loaded fast carry, fast rotation, or insertion is qualified.

There is still **no successful GPU installation, successful same-episode GPU
recovery, RAM grasp, or RAM installation**. Local controller progress must not be
reported as FLUX capability or completion of the full experiment sequence.

## Project and Prior Results

The environment is EmbodiedSWE/RoboBench PC assembly using a Franka Panda,
15 Hz control, three 640x360 RGB views and idealized calibrated simulator depth.
Control uses RGB/depth, robot proprioception/FK and execution receipts. Hidden
object poses, collision truth and evaluator feedback are excluded from decisions.
Native grading is kept separate. Upstream grasp-weld assistance remains enabled;
assisted grasps are not unassisted dexterity results. Camera changes are labeled
experimental conditions, not a physically qualified movable-camera rig.

Historical policy results (not a matched comparison after later fixes):

| Mode | Recorded result |
| --- | --- |
| Direct-A, medium | 23 GPT calls, 90 actions, no verified lift, native score 0 |
| Direct-B, medium | 20 GPT calls, 58 actions, no verified lift, native score 0 |
| Direct-A, high | 20 calls, 71 actions, no verified lift, native score 0 |
| FLUX+GPT Hybrid | Multiple short trials; no verified grasp. One closed/lifted the hand while the card stayed supported. |
| Hybrid followed by local correction | Accurate endpoints but partial card lift/tilt in that trial, not secure capture. |
| Later GPT-reviewed local DiffIK recipe | Assisted GPU lift and carry achieved; release tipped the card onto the motherboard. Native success false, score about 0.3333. |

Later camera/controller improvements benefited the local-controller trials.
These results cannot establish an intrinsic model ranking. The demonstrated
GPU carry/insertion attempt was not a successful native FLUX manipulation.
Recovery explored viewpoints, retreats and GraspGen-X proposals, but did not
recover the card. Visible contact access and proposal feasibility remained
problems; failure does not prove recovery physically impossible.

## Why Motion Was Slow

The original local target ramp used only **0.0225 m/s** translation and
**0.06 rad/s** rotation (about 3.4 degrees/s). A 30 cm translation therefore
requires at least 13.3 seconds and a 90-degree rotation about 26.2 seconds,
before settling. The recorded GPU lift/carry consumed 707+328 actions,
47.1+21.9 simulated seconds. These were conservative implementation limits,
not established physical requirements.

Intermediate fixed holds were removed: same-phase transit carries controller
state through waypoints, with per-action monitoring and phase-end settling.
This reduces pauses but does not by itself increase speed.

Rendering, depth capture and simulator execution still take roughly 6x simulated
time in recent runs. Videos labeled 1x simulated time exclude GPT/network waits.
The old direct controllers had a separate high GPT-call overhead. Current speed
tests made **zero paid model calls**: their bottleneck was local control.

## Recent RAM Work and Controller Diagnosis

RAM work improved camera visibility but did not produce a grasp. The latest
rear-module approach completed 249 actions, then open-hand preclosure took
504 actions and failed strict 3 mm arrival: target hand z=166.933 mm versus
actual z=162.612 mm. This was **4.320 mm downward overshoot**, not stopping above
the goal. No closure, lift, retry or threshold relaxation followed.

Rigid wrist-camera calibration plus terminal robot pose reconstructed the motion.
Replaying the old feedback law indicated about -6.364 mm accumulated downward
position-integral correction near target crossing. Commanded joint FK also
passed below the target. Integral windup was a supported contributor, not a
proof excluding all contact/dynamics effects.

Fix: clear an opposing per-axis position integral when target crossing exceeds
1 mm, retaining same-direction load compensation and a submillimeter deadband.
This subsequently passed an elevated unloaded GPU-condition test; lower-workspace
and payload behavior are not established by that test.

A separate evidence bug was found: a review prompt inherited holder height from
a previous module. That approval was discarded before execution. Without the
unsupported number, review requested inspection. Fresh current RGB-D samples
then supported exploratory placement, not certified hidden clearance. The prompt
now requires explicit current support samples. This is an important caution:
model review conclusions can be strongly influenced by asserted measurements.

RAM is now suspended by user direction. Do not restart it to avoid GPU-task work.

## Physical Speed Experiments

All tests used open hand, fixed orientation, a 12 cm elevated vertical excursion,
the GPU task, aimed-wrist configuration and unchanged per-action tracking guard.
The guard compares actual pose to the moving waypoint: 10 mm / 0.10 rad.
Arrival requires 3 mm / 0.03 rad. These checks are not collision certification.

| Condition | Outcome | Simulated / execution wall time | Endpoint errors |
| --- | --- | --- | --- |
| Conservative + anti-windup | Up/return passed, 209 actions | 13.933 s / 89.271 s | 0.080 / 0.074 mm |
| Smooth 5x, no feedforward | Stopped after 11 actions; ramp lag 11.093 mm | 0.733 s / 4.904 s | No arrival; 20.302 mm upward progress |
| Smooth 5x + feedforward | Up/return passed, 33+35 actions | 4.533 s / 29.313 s | 0.336 / 0.216 mm |
| Smooth 10x + feedforward | Stopped after 8 actions; no return/retry | 0.533 s / 3.452 s | No arrival |

The two 5x trials used fresh seed-0 episodes and the same path; feedforward
distinguishes them. The 10x test continued from the successful 5x return, so it
is not an independent matched-reset replicate. There are no multi-seed results.

The 5x no-feedforward stop did not hit the inner per-tick joint-command rate
cap: maximum commanded increment was 0.018153 rad versus the 0.06 rad cap.
That does not rule out actuator lag or every internal constraint. Full measured
joint trajectories were not logged. Feedforward improved the tested outcome,
but its performance elsewhere remains an empirical question.

### Implementation Details

- `transit_trajectory.py`: one synchronized quintic rest-to-rest time law across
  the whole move, with zero endpoint velocity/acceleration. Peak caps: 5x means
  0.1125 m/s and 0.30 rad/s; 10x means 0.225 m/s and 0.60 rad/s. Acceleration
  caps are 0.45 m/s2 and 1.2 rad/s2. These are candidate limits, not hardware certification.
- `NativeDiffIKFeedback`: optional one-step world-frame planned motion increment
  added to feedback, not accumulated into its integral. It is zero at the endpoint.
  Command caps and the actual tracking target remain unchanged.
- Fast profiles require elevated endpoints (z>=0.30 m), open measured/commanded
  grip, tracking guard and supported cadence. They are **not currently allowed
  for a closed-gripper loaded carry**. Do not silently remove this restriction.
- The smooth path must fit the action budget with settling allowance. Arrival
  requires four stable samples: endpoint precision plus <=0.5 mm and <=0.002 rad
  inter-sample motion. No mandatory consumption of all 64 actions.
- Each request remains bounded to 20 cm / 0.30 rad. The illustrative 30 cm timing
  estimate is an offline planner result, not an admitted current RPC request.
- A 30 cm 10x offline trajectory takes about **2.53 seconds**, including ramp-up
  and braking, before tracking/settling. Earlier 1.3-second wording was only a
  constant-speed lower bound and should not be quoted as demonstrated performance.

Latest suite: **282 passing tests**. Fake-plant, math and contract tests are not
physical qualification. The receipts above are the actual native evidence.

## Direct/Hybrid Plan: What Is Not Integrated Yet

The agreed direction is to let GPT choose bounded targets while local feedback
executes them between observations. Direct-A should retain incremental Cartesian
decisions and its memory semantics; Direct-B should retain absolute EEF decisions
and its history semantics. Larger target horizons are enhanced variants, not
unchanged upstream reproductions.

Hybrid already exposes accept/edit/eef/stop decisions. **Accepted FLUX joint
proposals must retain their action/timing semantics.** Edited EEF targets and GPT
EEF fallback may use the shared local executor, but their execution contribution
must be distinguished from native FLUX actions. Do not convert FLUX trajectories
to endpoint IK and then call the result native policy performance.

The qualification runner invokes `/local-stage`; the general `run_episode` loop
still calls `env.step` on policy action chunks. **The shared enhanced local-stage
execution path has not yet been connected to Direct-A/B/Hybrid.** This is a real
remaining implementation item, not just a pending experiment.

For a matched comparison, freeze cameras, task/seed, legal observation inputs,
model/reasoning, controller revision, motion profiles, assistance and budgets.
Log action source, actual low-level actions, GPT calls per meaningful stage,
simulated and wall time, overshoot, retention, placement and isolated native grade.
No final Direct-versus-Hybrid ranking is justified yet.

## Current Operations and Preserved State

Host: `ssh -p 45579 root@76.71.203.193`.
Remote repo: `/workspace/adaptive-physical-execution`.
Local repo: `/Users/macbookpro/Developer/random/gpu/adaptive_physical_execution`.
Two 24 GB RTX4090 GPUs; both nearly full with retained simulator workers.
FLUX is intentionally unloaded, not currently running alongside these tests.
Remote sources are manually synced; do not reset the remote checkout or assume
its Git HEAD describes the loaded code. Existing processes retain imported code.

Fresh read during handoff confirms current qualification observation
`4d39db60cb234fbf899be392416bddea:76` on worker86507, remote8774/local18774.
It is the **stopped 10x state**, not the successful 5x return at68. Do not retry
the failed action or automatically continue a qualification from it.

Fresh GPU process inventory:13434,54862,66502,79506,81115,86507. Older GPU recovery
is on66502 (last recorded observation2813); RAM comparison scenes79506 and81115
remain held. Their exact observation IDs were not freshly re-read for this report.
Keep user CPU workloads and other workers untouched.

User explicitly approved closing RAM baseline78152 after its2.3GB recordings
were checksum-backed up. Live physics state is gone; evidence remains. Temporary
qualification workers84047 and85321 were subsequently retired after saving results.
Several workers lingered after SIGTERM and required exact-PID SIGKILL. No broad
process killing, rental reboot or instance shutdown occurred.

Recordings are evidence, **not resumable physics checkpoints**. Do not promise
recovery of a terminated live scene from its videos. No credentials belong in
public artifacts. Existing private API budget/holds remain applicable if calls resume.

## Recommended Next Work

1. Stop serial speed sweeps for now. Use the passing5x unloaded vertical result
   as a starting point, not blanket qualification for every transit.
2. Implement the explicit shared local EEF execution option in the policy runner,
   including action-budget accounting, receipts/memory, no-retry stop propagation
   and preservation of native FLUX joint actions. Avoid hidden task recipes.
3. Resume useful GPU manipulation in a clearly labeled episode. Validate lateral
   transit/rotation and later payload retention only as needed along that task.
   Keep slower contact behavior; approach, closure and lift require current evidence.
4. Demonstrate actual grasp/retention/place with independent visual verification
   and isolated native grading. A successful speed probe is not a task phase.
5. Run one bounded matched enhanced Direct-A/B/Hybrid comparison, then a predefined
   same-episode recovery and execution-memory experiment if useful behavior exists.

Do not repeat unsupported holder assumptions, unchanged failed targets, prompt
wording sweeps, or many tiny tests instead of making manipulation progress.
The largest unresolved issues are task-level contact/placement, loaded control,
perception/access, and fair integration/comparison, not merely unit-test coverage.

## Evidence and Code Pointers

- [GPU-first plan](GPU_FAST_EXECUTION_PLAN.md)
- [Current implementation status](../IMPLEMENTATION_STATUS.md)
- [Older broad handoff](PROJECT_PROGRESS_HANDOFF_20260930.md)
- [RAM trial and overshoot evidence](RAM_FIRST_TRIAL.md)
- [Conservative return receipt](evidence/gpu_antiwindup_209/3_receipt.json)
- [5x without feedforward stop](evidence/gpu_fast5_11/0_receipt.json)
- [5x feedforward up](evidence/gpu_fast_ff/0_receipt.json)
- [5x feedforward return](evidence/gpu_fast_ff/1_receipt.json)
- [10x feedforward stop](evidence/gpu_fast_ff/10x_stop_receipt.json)
- Local video: `runs/gpu_fast_ff_1x.mp4`,1x simulated time, model waits excluded.
  Shows successful5x up/return followed by the short stopped10x attempt.
- Relevant code: `src/physical_exec/{osc_reference,transit_trajectory,local_stage}.py`,
  `src/physical_exec/backends/embodiedswe.py`, `scripts/probe_local_stage_service.py`.
- Latest experiment commit: `18c0ea9`; feedforward implementation:`92e2c78`;
  smooth-path integration:`83f58ad`; conservative native qualification:`6b0d5bb`.

Bottom line: there is now a concrete, measured local-motion speed improvement.
There is not yet a successful installation or robust autonomous recovery, and
the faster executor has not yet been evaluated as part of matched policy modes.
