# Same-episode local correction bridge

Added opt-in `serve_embodiedswe.py --allow-local-stages` and `/local-stage` RPC.
The default worker remains unchanged. Requests bind the exact current observation,
target hand pose, gripper opening, bounded action count, and explicit provenance.
Targets are limited to the pilot workcell, 20 cm / 0.30 rad from current pose,
and 1..64 control actions. These are simulation bounds, not clearance certificates.

The operation runs the upstream native DiffIK solver against live robot state,
using the previously tested bounded translation-integral feedback helper and
0.0225 m/s target ramp. Its joint targets pass through the existing joint tracker,
joint-step/URDF validation, orientation and near-joint-limit stops. No object state
or collision oracle enters control. Grasp assistance remains enabled by the scene.
This 15 Hz integration differs from the earlier 48 Hz standalone native pilot.

Commands are deduplicated by ID including route; changed reuse is rejected.
Execution errors poison the worker and must not be retried. Stages execute their
declared bounded action count (unless host success ends execution); pose arrival
is checked afterward. Arrival says nothing about grasp, aperture settling, or
successful contact. A budget-ended stage must not be called successful arrival.

## Live qualification

First run `local_stage_bridge_20260930` held for 30 actions, then completed 90
offset actions but failed constructing its receipt: `ExecutionReceipt` permits
at most 64 steps. The worker halted; the motion was NOT retried. Raw captures and
per-latch command records are retained locally. The endpoint now rejects >64
before motion, with regression coverage. No global receipt bound was relaxed.
Added failure journaling afterward; that error-journal addition was not exercised
by the successful live run below.

Fresh run `local_stage_fixed_20260930`, episode
`7425f3cdce5d426a9213110dfcea8d91`:

- Hold: 30 actions / 2 sim seconds, recorded position error 0.
- Upward 1 cm: 60 actions / 4 sim seconds, position error 0.246 mm,
  rotation error 0.0000749 rad; arrival passed.
- Zero model/API calls; execution wall time 13.765 + 26.077 seconds.
- No object contact intended. This qualifies only a small unloaded offset,
  not payload motion, arbitrary directions, grasp correction, or task completion.

Evidence: `docs/evidence/local_stage_fixed_20260930`; both full simulator recordings
are backed up locally. 160 CPU tests cover request bounds, opt-in, deduplication,
and existing behavior; these do not qualify manipulation. The next meaningful
test is Hybrid -> fresh RGB-D target -> bounded local correction in the SAME
episode, with model/operator roles disclosed. Do not replay a successful scripted
grasp and label that adaptive recovery.
