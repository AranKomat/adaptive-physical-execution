# Implementation status / next-agent handoff

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
