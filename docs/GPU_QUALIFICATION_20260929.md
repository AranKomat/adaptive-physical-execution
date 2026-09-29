# First GPU qualification (2026-09-29)

## Completed

- Single RTX 4090, 24 GB; separate Isaac, FLUX, and orchestrator environments.
- CPU regression suite: 90 passed after the integration fix (previously 86).
- Earlier upstream FLUX tests: 174 passed, 5 skipped.
- Captured seed-0 PC GPU assembly scene through the real simulator worker.
- Reset's robot-only URDF FK comparison passed; three distinct camera PNGs saved.
- Standalone FLUX DROID `variants/gd-fp8r` inference completed on this capture.
- No paid model calls or robot action chunks executed during these probes.

## Fixes and failures

The host lacked `libGLU.so.1`; installing `libglu1-mesa` removed those renderer
errors. A subsequent apparent startup stall was actually Isaac cleanup blocking
after an exception. The launcher now prints the exception before cleanup.

The real integration exception was `zero joint axis`: upstream's fixed
`panda_joint8` legitimately specifies a zero axis. The parser now ignores the
axis for fixed joints and continues rejecting zero axes for actuated joints.
Four regression cases cover that distinction. Failed shutdown processes needed
termination; shutdown behavior remains an operational issue to investigate.

The first standalone FLUX proposal was rejected by the canonical gripper range
check. A second diagnostic run retained the raw output without clipping:

| Measurement | Result |
|---|---:|
| Package loading | 19.34 s |
| First prediction | 1.424 s |
| Output shape | 1 x 32 x 8 |
| Raw closed fraction minimum | -0.0044595 |
| Raw closed fraction maximum | 0.0701137 |
| Peak PyTorch allocation | 22,549,724,672 bytes (21.0 GiB) |
| Peak PyTorch reservation | 23,853,006,848 bytes (22.2 GiB) |

These are one-run measurements, not latency percentiles or steady-state results.
Isaac used approximately 7.3 GiB after capture. The current resident processes
therefore do not have a credible shared 24 GB budget; separate GPUs are recommended.
No simultaneous out-of-memory experiment was needed to reach that recommendation.

## Evidence and limitations

Local and remote retained artifacts (under ignored `runs/`):

- `gpu_capture_fixed_axis_20260929/`: camera PNGs, observation, metadata.
- `flux_capture_probe_diagnostic_20260929/`: raw proposal and metrics.

The left camera sees the loose card but has arm occlusion; the wrist camera crops
the card; the right camera sees the case interior. Rendering works, but these
camera placements are not qualified as DROID-distribution matches.

The native scene has `grasp_weld=true`. No task success, grasp, useful motion,
FLUX FK-path qualification, or closed-loop GPT result has been demonstrated.
The small gripper overshoot must be investigated against upstream output semantics;
it is not by itself evidence that the policy cannot solve the task. The strict
execution boundary remains unchanged.

## Next

1. On two GPUs, isolate Isaac and FLUX; do not change upstream revisions.
2. Resolve the gripper output convention explicitly before admitting proposals.
3. Qualify full proposal joint bounds and robot-only FK paths.
4. Run the planned three-decision Direct-A trial on a fresh worker.
5. Run bounded Hybrid only after proposal qualification, then matched comparisons.

`scripts/probe_flux_capture.py` reproduces proposal-only diagnostics from a retained
capture without simulator access or robot motion. It does not qualify execution.
