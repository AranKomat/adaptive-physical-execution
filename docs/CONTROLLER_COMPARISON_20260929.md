# Matched free-space IK comparison

Question: is the custom IK adapter grossly miscalibrated relative to upstream?
Two fresh seed-0 PC GPU episodes used identical initial joints and hand poses
(exact JSON numeric equality), the same 15 Hz outer cadence, camera setup, joint
PD robot and actuator limits. The target was initial hand position plus
(0.06,0,-0.06) m, unchanged orientation, open gripper. The local loop replanned
at most 1 cm from measured position per action with a 60-action cap and 3 mm
arrival criterion. No object state or language-model calls were used.

| Path | Actions | Final target error | Execution wall time |
|---|---:|---:|---:|
| Upstream DiffIK algorithm | 32 | 2.521 mm | 15.36 s |
| Integrated URDF iterative IK | 31 | 2.220 mm | 13.99 s |

Both completed without rejection. Evidence is retained under
`runs/native_ik_probe_20260929` and `runs/integrated_ik_probe_20260929`, including
initial states, per-step joints/receipts/errors, and rendered recordings.
Reproduction entrypoint: `scripts/compare_ik_probe.py` in the Isaac environment.

## Interpretation and limitations

There is no gross free-space reaching disadvantage demonstrated for our adapter
on this target. This does NOT prove accurate contact dynamics, grasp geometry,
camera-to-object grounding, controller robustness, or general superiority.
The one-action difference and wall-time difference are not statistically meaningful.

The native arm controller uses upstream Isaac Jacobians, DLS damping, persistent
joint-command integration and lead/joint clamps. Its emitted joint commands were
passed through our unchanged execution guards into the same joint-position plant.
This is an algorithm comparison at matched 15 Hz, NOT a full unchanged native
DiffIK-mode rollout at its default 50 Hz controller cadence. Full cadence and
contact comparisons remain open. The previous constrained-grasp worker was left
untouched; each diagnostic used a separate process/episode on GPU 0. Shared GPU
load makes wall-time comparisons particularly weak.

The upstream `pc_gpu_smoke.py` is NOT a Franka baseline: it selects `robot="null"`
and applies forces directly to the card using privileged geometry. Running it
could validate scene mechanics, but cannot demonstrate robot grasp competence.
Do not substitute its success for an unchanged upstream robot solution.

Next: do not repeat free-space microdiagnostics. Contact-capable native reference
and actual Hybrid execution remain the unresolved comparisons. No task success,
successful recovery or completed upstream reproduction is claimed here.
