# Guarded lift and carry: current continuation

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
