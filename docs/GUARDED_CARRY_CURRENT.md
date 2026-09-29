# Guarded lift and carry: current continuation

## Standoff execution correction

The history-based standoff planner now declares `local_stage_continuous` and
the full compiled budget (128 actions maximum for8cm, not a single64-action
dispatch). `run_sensor_carry.py --standoff-review <review.json>` validates the
current plan/review,15Hz cadence, preserved grip/lateral pose, attitude bound,
and predicted gap before dispatch. Segments are at most5cm; intermediate
segments pass through and only the endpoint settles. Tracking guard is required
on every segment. Legacy budget-mismatched candidates are rejected, not silently
reinterpreted. This does not retroactively approve/replay the1355 timeout.

Guard settings are now included in the carry's predeclared sequence as well as
individual requests.224 CPU tests pass, including stale/refused review, timing,
grip and lateral-motion rejection. No new physical result follows from these
tests. Existing wrist imagery at1355 still lacks a clear lower mating edge.

## Latest: partial closer standoff at 1355

One lower oblique camera move (eye [0.65,0.40,0.40], gaze
[0.47224265,0.02802998,0.25]) completed64 hold actions to1291, with
0.872mm/0.002116rad arm error. The cooler still obscured the connector;
no further camera sweep was launched.

Astra reviewed an8cm closer standoff using observation835 held-feature depth
propagated with current robot pose, explicitly assuming no slip. Predicted
remaining feature-to-socket gap was148.745mm, not measured clearance.
Review approved only this exploratory closer look ($0.01927125).

The executed local stage used64 actions, retaining the exact previous gripper
command and native contact tracking guard. At1355 it ended4.306mm short with
0.001432rad rotation error: **budget ended without strict arrival**, not a guard
stop. No retry, insertion or release. The planning candidate allowed more time
than the local64-action executor; this execution-budget mismatch must be fixed
before reusing that path. Do not infer a physical obstruction from timeout alone.
One earlier pre-dispatch assertion rejected float32 grip readback; no motion
was issued then. The actual command preserved readback0.30000001192092896.

Current image suggests retention but still hides the mating edge. Preserve the
held episode at1355, inspect existing wrist/history evidence before another
action, and do not count this as successful standoff arrival. Local artifacts:
`runs/guarded_full_lift_20261001_connector_view`, `_closer_standoff`,
`_standoff_review`, `_standoff_execution`, and `_capture1355`.

The1227 state described below is historical.

Artifacts retain the `guarded_full_lift_20261001` prefix; this is a run name,
not an independently verified calendar timestamp.

Episode `9fbd76d8e57641c79983eed82adbc2bc` is held at observation 1227 on
worker port 8768. A fresh read-only capture confirmed this state after the
continuous-transit default change. No new motion was issued in this continuation.

## Physical results retained from this episode

- Explicit 23 cm lift, not the earlier default 5 cm: approach, closure and lift
  completed in 707 actions. Final lift error was 2.351 mm / 0.000137 rad.
- Reviewed elevated carry completed in 328 actions, ending at observation 1163,
  with 1.912 mm / 0.000411 rad endpoint error. No tracking-guard stop.
- Subsequent inspection-camera hold ended at 1227. No descent, insertion or
  release has occurred. Grasp assistance, cached target pixels remeasured on
  fresh depth, operator-defined motion, and unknown clearance remain disclosed.
- The correction runner used exploratory phase-completion bounds, even though
  the recorded final lift also met strict endpoint tolerances. Endpoint arrival
  alone is not task success or proof of retention.

These results supersede a generic payload-failure diagnosis. The earlier
open-gripper baseline was not configuration-matched to the held-card stall;
controller reset was another confound. The cause of that earlier stall remains
unresolved. Do not call the comparison causal or repeat it merely to accumulate
component evidence.

## Latest perception evidence

One Astra Flex medium feature-inventory call used the current images plus the
earlier observation-835 carry selection and a legally derived projected anchor.
It identified the same socket housing, but could not expose the held connector.
Right-view pixels [294,243] and [335,229] passed unrefined 3x3 depth sampling:

- World surfaces: [0.50973115,0.02696612,0.03785890] and
  [0.45099615,0.03033837,0.03786709] m.
- Local depth spreads: 1.985 and 2.064 mm; sample separation 58.832 mm.
- These are surface-axis samples, not mating endpoints, calibrated uncertainty,
  a slot centerline, or insertion authorization. Connector samples are empty.

The call settled at $0.04208375. Two launcher failures preceded it before any
HTTP request (wrong file path, then existing audit directory); neither was an
API retry. Existing budget ceiling and unresolved holds remain unchanged.

## Next action and phase status

Preserve this episode and socket history. Resolve the held connector using a
deliberately selected legal view or tracked prior feature, with explicit
uncertainty; do not repeat socket rediscovery or descend from rim samples alone.
Insertion/release, successful adaptive recovery, and routing/memory comparisons
remain incomplete. This is improved component execution, not a completed phase
or a full nonprivileged task solution.

Local evidence: `runs/guarded_full_lift_20261001_execution`, `_carry_execution`,
`_capture1227_flat`, `_inventory_history_review_validated`, and
`_inventory_measured.json`. Read-only reconfirmation:
`runs/continuous_default_resume_capture`.
