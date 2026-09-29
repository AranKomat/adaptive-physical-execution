# Contact tracking and phase-specific completion

## Predeclared trial

Following the user's clarification that grasp/carry need not demand insertion
alignment, distinguish hand tracking error from object tilt. A card can be
slanted and still securely retained; neither nominal EEF arrival nor aperture
alone proves that retention.

Prior closure reconstruction from the calibrated rigid wrist camera agrees
with measured final hand pose within 0.001 mm / 0.000001 rad. Last-second motion
diameters: 2.044 mm translation, 0.002616 rad rotation. This supports testing a
bounded angular bias compensator, not a claim of force stability or grasp success.

Fresh `contact_integral_20260930` uses the same cached right-image target on fresh
depth, wrist-aim camera condition, approach sequence, and unknown-clearance
simulator-only scope. No privileged object state or new target-selection call.
Opt-in native DiffIK rotation integral: gain 0.525/s, per-axis cap 0.03 rad;
existing 0.05 rad command cap and worker abort checks unchanged. Default off.

Contact probe completion is declared separately: all 64 actions executed,
position tracking error <= 10 mm and rotation error <= 0.15 rad. This is a
bounded exploratory-motion criterion, not certification of contact, object tilt,
grasp success or insertion readiness. Raw precision-arrival receipts remain
unchanged. Ambiguous, aborted or incomplete execution is never accepted.

Both controller feedback and completion policy change in this trial; do not
claim a clean success-rate ablation. Compare raw errors for controller behavior,
and use actual lift/retention images for the physical result. Attempt at most
one closure, inspect, and then at most one 5 cm lift if the declared conditions
hold; stop on ambiguous execution or failed bounds without retry.

## Outcome

Episode `edd9f171c42a44558e2f30a930e7a088`: ten open approach stages
executed 640 actions and passed all arrival checks (final 1.183 mm).
Closure executed 64/64 actions: 1.759 mm / 0.010346 rad error, passing
even the original precision arrival threshold. One subsequent 5 cm lift
executed 64/64 actions: 4.714 mm / 0.033413 rad error. It passed the
predeclared exploratory completion bounds but not precision arrival.
No retry or further motion was issued.

Before/after images suggest upward card movement with the hand, but complete
support clearance and secure retention are not established. No independent
review was requested and no paid calls were made. Grasp assistance remains on;
this is an operator-authored, cached-target replay, not autonomous recovery.
Object tilt is not itself a grasp failure; it is distinct from hand tracking
error. Insertion alignment and retention still require separate evidence.

Local artifacts: `runs/contact_integral_20260930_{approach,close,lift}` and
`runs/contact_integral_20260930_recordings`. CPU regression: 176 tests passed.
