# Implementation status / next-agent handoff

## Current experiment status (September 30 JST)

- Native GPU simulation, robot FK, live Astra Flex calls and FLUX prediction/FK
  qualification have run. Actual FLUX Hybrid manipulation remains untested.
- Frozen privileged OSC reference replay succeeded through seating/release/retract
  in 1,859 actions, zero calls. This is not nonprivileged success.
- Sensor-target OSC captured/lifted with assistance but lost orientation (2.591 rad).
- Native DiffIK preserved orientation but initially fell 99 mm short of lift.
  Bounded translation integral plus a larger error cap then achieved a controlled
  assisted lift (1.945 mm, 0.02094 rad) and elevated carry (1.661 mm, 0.01778 rad).
- Nonprivileged insertion, completed task, adaptive recovery, matched mode comparisons
  and experience reuse remain OPEN. Mating-feature visibility is the current issue,
  not evidence that all motor control or perception problems are solved.
- The bounded sensor pilot ended at 3,130 actions, held=true but task=false.
  Two alignment reviews requested inspection; no insertion was attempted.
  Its 74 MB trace is backed up locally, with compact public evidence and video.
- The earlier next step was pre-grasp socket localization and retained geometry;
  coarse localization has since run, but precise entry geometry remains open.
- An explicitly changed overhead-right-camera condition exposed a candidate
  socket before carry. Lift/carry repeated, but hand/card occlusion remained
  afterward; a historical-context review recognized the prior socket without
  claiming present alignment. No insertion yet. See `docs/OVERHEAD_SOCKET_20260930.md`.
- Independent camera translation is now opt-in and live-tested while the arm
  holds. A Fabric-backed pose failure was detected; the pinned USD pose route
  passed. The idealized camera has no collision body. Post-carry use is recorded
  below; see `docs/INSPECTION_CAMERA_20260930.md` for the initial qualification.
- Post-carry independent views now supported a fresh contact-edge measurement,
  two reviewed closer approaches and one contact-intended attempt. All endpoints
  passed, but the native seating predicate remained false and the card stayed
  held. Four fresh calls cost $0.08531625. Precise correspondence remains unresolved;
  see `docs/POST_CARRY_CONTACT_20260930.md`. No release or successful recovery yet.
- 144 CPU tests pass. They do not establish manipulation robustness.
- Next: obtain corresponding connector/slot endpoints or axes from legal images
  and depth, then attempt one bounded alignment/recovery. Do not compensate for
  uncertain correspondence by pressing farther down.

See [native DiffIK evidence](docs/SENSOR_DIFFIK_PILOT_20260929.md),
[stage sequence](docs/STAGE_EXECUTION_20260929.md), and
[privileged reference audit](docs/REFERENCE_TRANSFER_20260929.md).
All sensor pilots retain grasp assistance and unknown swept clearance. They use
operator-defined phase recipes and are not autonomous full-task success claims.

## Original pre-GPU build snapshot

The sections below record the original delivery, not current GPU progress.
**Build:** 2026-09-29, version 0.1.0.

## Completed and tested on CPU

- Typed single-arm observation/action/receipt contracts; open-vs-closed gripper conversion.
- World-frame SE(3) action integration; wxyz quaternion handling; Euclidean motion bounds.
- Robot-only URDF FK, Jacobian, damped IK, joint limits and continuity validation.
- Exact upstream RoboICL anchored-memory helper, with immutable execution records and gaps.
- Single-arm direct-delta, direct-absolute, and hybrid reviewer/controller ports.
- Explicitly configured Responses client with strict action schema, usage accounting,
  time/call budgets, and no implicit endpoint/model fallback or execution retry.
- Authenticated loopback worker transport; one episode per simulator worker; duplicate
  command handling; stale-observation rejection; ambiguous-execution stop behavior.
- Complete fixture rollouts through all three modes, both in-process and over loopback HTTP.
- Policy-context allowlisting with tests that host-only evaluator sentinels never enter requests.
- Event/frame integrity checks, self-contained HTML reports, descriptive CSV/JSON comparison.
- Task configurations, pinned source-fetch plan, native RoboICL profile generator, documentation.

The exact test output and counts for this delivered build are in **VALIDATION.md**.

## Implemented but not exercised against the real dependency

**EmbodiedSWE GPU worker.** Uses the pinned `EvalSim` API, adds two explicit exterior
cameras plus the real wrist view, reads robot proprioception, qualifies FK, executes joint
commands, runs the native grader outside the policy context, and writes per-latch frames.
No Isaac Sim environment, assets, graphics driver, or real contact dynamics were available here.

**FLUX worker.** Calls the inspected standalone DROID policy API. Camera/state conversion
is unit-tested, but no checkpoint/encoder has been loaded and no FLUX output produced here.
Camera distributions, source rate, target dynamics, and task competence remain unknown.

**Live GPT client.** Request/response/error behavior is tested with HTTP mocks only.
No paid endpoint/model, xhigh/medium comparison, account access, or latency measurement occurred.

**Campaign supervisor and continuous video command.** Written and syntax/CLI checked.
A native GPU campaign and native rollout video have not been executed.

## Not implemented / intentionally deferred

- Exact end-to-end reproduction of the dual-arm RoboICL benchmark or full Codex Direct runtime.
  We preserve source pins and provide a native-profile helper, but our single-arm ports differ.
- Automatic memory-summary generation/retrieval optimization. A typed unverified-summary hook
  exists; no compression model, learned summarizer, or benefit claim exists.
- Automatic Hybrid→Direct mode switching or multi-proposal execution without GPT review.
- Task-specific post-training, policy distillation, force/tactile controllers, collision-aware
  motion planning, automatic calibration, real2sim reconstruction, real hardware operation.
- A demonstrated GPU, RAM, bulb, or other manipulation success. **None has been observed here.**
- Quantified robustness, recovery improvement, latency improvement, ROI, or sim-to-real transfer.

## Source findings that affect the plan

1. The GPU scene enables grasp welding by default. Preserve/record it and disclose it; do not
   describe a successful assisted grasp as unassisted physical generalization.
2. FLUX DROID emits joint targets, not EEF deltas. It requires three distinct views and a
   matching Panda joint order. Its PC-assembly competence is unverified.
3. The published RoboICL profile uses a third-party API endpoint/alias. The package never
   forwards credentials there implicitly.
4. The original full Codex direct agent is different from the constrained single-Act Direct-B
   port. Treat this as a changed experimental condition.
5. The environment pauses while reasoning occurs. Video simulated-time speed is not wall time.

## First hour on the GPU machine

1. Fetch/check the pins and install the upstream simulator environment.
2. Run one **capture-only** GPU scene. Check camera coverage and the FK qualification.
3. Restart the worker. Run Direct-A for just 3 decisions to test API/schema/control plumbing.
4. Independently load FLUX in its separate environment. Probe its output on a captured scene
   without execution. Inspect joint/FK magnitudes and the camera contract.
5. Only then run a small Hybrid trial. Use `pc_gpu`; add `pc_ram` after the bridge is behaving.

Stop and fix an interface or dynamics issue before running long episodes. Do not run broad
benchmark sweeps, download every dataset, or port to another GPU software stack first.

## Most likely GPU-side fixes needed

- Camera coverage and physical camera calibration differ from the model's training rig.
- Isaac renderer/plugin setup or assets may require environment-specific installation.
- Panda URDF/root/hand-frame mismatch may trigger FK qualification; investigate, do not bypass.
- Joint-PD/IK may lack the contact behavior needed for insertion/threading. The source offers
  OSC/impedance modes, but this release does not implement equivalent joint-policy/EEF mixed
  control over those modes. Any change must be separately logged/qualified.
- FLUX dependencies and referenced encoder caches must match its pinned environment.
- Provider Responses compatibility and exact model ID need your account-specific verification.

## Validation interpretation

A CPU fixture pass means the software loop is internally consistent. It says nothing about
whether the visual model recognizes the component, whether the motor policy generalizes, or
whether contact dynamics permit the task. Keep `examples/cpu_fixture` out of investor robot
videos; those examples exist solely to make the implementation inspectable without a GPU.
