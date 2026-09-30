# Research Handoff: Shared Local Execution Integration

Date: September 30, 2026 (JST).
Repository: https://github.com/AranKomat/adaptive-physical-execution

This is a self-contained update since
[the previous GPU-speed handoff](RESEARCH_HANDOFF_GPU_SPEED_20260930.md), which
recorded experiment snapshot `18c0ea9`. The previous report was committed as
`d0ea6e1`; shared execution was subsequently committed as `c17093c`.
This report accompanies the following opt-in fast-profile integration.

Subsequent planning decision after external feedback: use the implemented fast
option as the standard configuration for eligible transit in the next enhanced
GPU trials, rather than repeatedly choosing the slow profile. The generic CLI
remains opt-in; launcher wiring is pending. Contact and closed-grip transport
remain conservative until separately tested. See the authoritative top section
of [the experiment plan](GPU_FAST_EXECUTION_PLAN.md). No new physical results.

## Bottom Line

Since the previous report, progress is **software integration, not a new physical
success**. Direct-A, Direct-B, and Hybrid EEF fallback can now send a single
destination to the guarded local DiffIK executor instead of requiring GPT to
issue each small control action. An explicit fast-open-transit option selects
the previously tested 5x profile within its restricted scope.

There has been **no new live-model enhanced trial, successful installation,
loaded fast carry, or successful recovery** in this interval. The central
hypothesis remains untested: whether this integration substantially reduces GPT
calls while preserving useful manipulation performance.

## Context and Objective

The project studies adaptive physical execution on the EmbodiedSWE/RoboBench
PC-assembly simulator with a Franka Panda. The current priority is **GPU-card
installation, not RAM**, followed by a fair comparison of:

- Direct-A: incremental Cartesian decisions with execution-grounded memory.
- Direct-B: absolute end-effector (EEF) targets with its own history semantics.
- Hybrid: FLUX joint proposals reviewed by GPT, with EEF alternatives/fallback.

The user wants useful manipulation with only a few GPT decisions per meaningful
stage, substantially faster transit (a 5-10x target), and less time spent on
isolated microdiagnostics. A local controller may execute and monitor a selected
target; it must not secretly choose the grasp or supply a scripted task solution.

Control inputs are RGB, calibrated simulator depth, proprioception, robot-only
FK and execution receipts. Hidden object poses, collision truth and native
evaluation remain excluded from control. Depth is an idealized sensor condition,
not evidence of real-camera robustness. Upstream grasp-weld assistance is still
enabled and must be disclosed. All work is simulation-only.

## Prior Physical Evidence Still Applicable

These are retained results, **not experiments newly run for this report**.

| Experiment | Result | Important limitation |
| --- | --- | --- |
| Historical Direct-A, medium | 23 GPT calls, 90 actions; no verified lift; score 0 | Predates later controller/camera improvements |
| Historical Direct-B, medium | 20 calls, 58 actions; no verified lift; score 0 | Not matched against the improved local executor |
| Historical Direct-A, high | 20 calls, 71 actions; no verified lift; score 0 | Does not establish reasoning-effort causality |
| Short FLUX+GPT trials | No verified grasp | Not evidence that local-IK success is FLUX success |
| GPT-reviewed local DiffIK recipe | Assisted GPU lift/carry; release tipped card onto motherboard; native score about 0.3333 | Installation failed; subsequent recovery unsuccessful |
| Conservative anti-windup up/return | 209 actions; 13.933 simulated / 89.271 wall seconds; endpoint errors 0.080/0.074 mm | Elevated, unloaded vertical motion only |
| Smooth 5x without feedforward | Tracking guard stopped at action 11; 11.093 mm moving-target lag | No arrival |
| Smooth 5x with feedforward | 68 actions; 4.533 simulated / 29.313 wall seconds; errors 0.336/0.216 mm | One unloaded vertical up/return; not loaded transport |
| Smooth 10x with feedforward | Tracking guard stopped after 8 actions | Continued from the successful 5x return; no retry/return |

The passing 5x-cap run was **3.07x faster in total simulated execution**, not a
5x task speedup. Acceleration, braking and settling reduce the realized gain.
Recent simulator execution was roughly 6x slower than simulated time; speeding
robot motion does not eliminate rendering/depth/simulator wall-time overhead.
No successful GPU installation or RAM grasp/installation has been established.

## What Changed Since the Last Handoff

### Shared EEF Executor: Implemented

`physical-exec run --local-eef-execution` now routes exactly one EEF destination
through `/local-stage`:

- Direct-A deltas pass through existing validation and become absolute targets.
- Direct-B retains absolute-target decisions.
- Hybrid EEF alternatives use the local executor. Accepted native FLUX joint
  sequences still use the original execution path and timing.
- Multi-target EEF output is rejected before budget truncation.
- A request permits at most 64 low-level actions, further bounded by the
  remaining run budget. Actual executed actions, not destination count, consume
  the budget.
- Guard stops and nonarrival terminate the run without an automatic retry.
- Traces preserve the local request, policy source, proposal ID and receipt.
- Memory distinguishes one destination from its multiple low-level actions.
- Direct modes default to horizon 1 when the enhanced option is selected.

This supersedes the previous report's statement that the policy runner still
lacks local-stage integration. It is an **enhanced variant**, not unchanged
upstream reproduction and not a new learned action policy.

### Fast Open Transit: Implemented, Not Live-Integrated-Tested

`--fast-open-transit` requires enhanced execution and a worker advertising both
the 5x profile and optional one-step feedforward. For an EEF destination it
selects smooth 5x with feedforward only when:

- Measured gripper openness is at least 0.999 and commanded openness is 1.
- Current and destination hand heights are both at least 0.30 m.

Other local moves retain the conservative profile. Native FLUX joint accepts
are unchanged. The manifest and model prompt disclose the option and scope.
These conditions **do not certify obstacle clearance**, nor establish that
arbitrary lateral motion or rotation will track successfully.

Underlying local bounds remain 20 cm / 0.30 rad per request, with tracking
guards unchanged. The 5x caps are 0.1125 m/s and 0.30 rad/s, using a continuous
quintic trajectory, acceleration limits and stable endpoint settling. Closed-hand
payload motion is not enabled for the fast profile. No 10x default was adopted.

### Verification

Fresh local verification for this handoff: **306 tests passed in 8.54 seconds**
using `../internal/physical-ai-lab/.venv/bin/python -m pytest -q`.
Tests exercise local routing, budgets, stop propagation, profile selection and
preservation of native hybrid joint execution. Fixture tests are not simulator
or payload qualification. No simulator actions or paid calls were made while
preparing this report.

## Remaining Integration Gaps

1. **Private paid-call launcher still uses the old contract.**
   `internal/physical-ai-lab/scripts/run_adaptive_direct_trial.py` only accepts
   local simulator ports 18765/18767, uses Direct horizons 5/3, and budgets only
   five control steps per Direct decision. It does not yet expose the enhanced
   execution options or qualification worker port 18774. Extend this launcher
   without bypassing its shared spending ledger, existing holds or route rules.
2. **The GPU task still permits only 3 cm translation per EEF target.**
   `configs/tasks/pc_gpu_grasp_wrist_aim.json` retains `max_translation_m: 0.03`.
   Shared execution alone therefore does not deliver the intended large reduction
   in decision count. Define explicit bounded enhanced-target limits rather than
   silently modifying baseline or native FLUX semantics.
3. **No end-to-end live-model verification of the integrated path.**
   Passing the standalone motion probe does not verify model target choice,
   perception, memory behavior, loaded tracking, contact or installation.
4. **GPU capacity is occupied by retained simulator scenes.**
   FLUX was unloaded during speed work. A matched Hybrid trial needs capacity
   planning and restoration, not an assumption that FLUX is already resident.

## Recommended Next Sequence

1. Finish the launcher and explicit enhanced-target configuration, preserving
   low-level action accounting, paid-call limits and provenance.
2. Archive the temporary stopped speed-test worker's evidence and use a fresh,
   clearly labeled GPU episode. Do not automatically resume the failed 10x move.
3. Run a bounded enhanced Direct trial toward an actual GPU approach/grasp.
   Use current legal observations; do not replay old pixel/hidden coordinates.
   Validate lateral/rotational motion as needed for the task, not a broad sweep.
4. Verify closure, lift and retention before transport. Qualify loaded faster
   motion separately; keep contact/insertion conservative initially.
5. Run matched enhanced Direct-A/B/Hybrid trials with frozen task/seed, cameras,
   depth, model/reasoning, execution revision, assistance and budgets. Report
   execution source so native FLUX actions and local EEF fallback stay distinct.
6. Evaluate a predefined same-episode recovery and execution-memory reuse after
   useful manipulation. Do not substitute answer-only tests for physical effects.

Record calls per meaningful stage, actual actions, simulated/wall time, cost,
guards, endpoint errors, grasp/retention/place and isolated native grade. Avoid
a model ranking from historical trials with different controller/camera setups.

## Operational Continuation Notes

Last recorded GPU host: `ssh -p 45579 root@76.71.203.193`.
Remote checkout: `/workspace/adaptive-physical-execution`.
Remote sources are manually synced; do not reset the dirty checkout or assume
Git HEAD describes code already imported by a running worker.

**The following live state is inherited from the prior handoff, not freshly
polled for this report. Recheck before acting.** Temporary worker 86507 on remote
8774/local 18774 ended at observation
`4d39db60cb234fbf899be392416bddea:76`, the stopped 10x state, not successful
return 68. Older retained workers were 13434, 54862, 66502, 79506 and 81115;
66502 held the GPU recovery scene. Preserve unrelated CPU work and retained
scenes. Recordings are not resumable physics checkpoints.

Paid inference uses the private authorized launcher and shared $75 ledger with
unresolved holds. Re-read its authoritative state before new calls; no new
spending ceiling is implied here. The recent route was Astra Flex, medium.
No credentials should appear in public reports or commits.

## Evidence and Entry Points

- [Previous detailed handoff](RESEARCH_HANDOFF_GPU_SPEED_20260930.md)
- [Older project-wide handoff](PROJECT_PROGRESS_HANDOFF_20260930.md)
- [5x up receipt](evidence/gpu_fast_ff/0_receipt.json)
- [5x return receipt](evidence/gpu_fast_ff/1_receipt.json)
- [10x stop receipt](evidence/gpu_fast_ff/10x_stop_receipt.json)
- [Runner](../src/physical_exec/runner.py)
- [Model prompt and controller ports](../src/physical_exec/controllers/ports.py)
- [Local execution tests](../tests/test_local_policy_execution.py)
- Local video: `runs/gpu_fast_ff_1x.mp4` (1x simulated time, not wall time).

Assessment: separating occasional GPT target selection from continuous local
control is promising and now connected in code. Useful assisted manipulation
has prior evidence, but robust placement/recovery and the improved policy
comparison remain open. The immediate priority is an integrated task trial,
not more architecture or another unconstrained speed sweep.
