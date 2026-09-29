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
support clearance and secure retention are not established. No paid calls were
made during execution; a subsequent separate visual review is recorded below.
Grasp assistance remains on;
this is an operator-authored, cached-target replay, not autonomous recovery.
Object tilt is not itself a grasp failure; it is distinct from hand tracking
error. Insertion alignment and retention still require separate evidence.

Local artifacts: `runs/contact_integral_20260930_{approach,close,lift}` and
`runs/contact_integral_20260930_recordings`. CPU regression: 176 tests passed.

## Subsequent review and next decision

One Astra Flex medium review saw nine images: left/right/wrist before closure,
after closure and after lift, with observation IDs but no hidden object state or
suggested verdict. It returned `partial_contact`: upward movement is visible,
but no continuous gap beneath the entire card; one end may remain supported.
The result is visual evidence, not a definitive contact measurement. Cost
$0.02803375; no further robot motion was issued.

Comparison with `sensor_diffik_integral_20260930/command_1.json` exposes major
confounds before attributing this outcome to the controller:

- Successful pilot remeasured a wrist target after approaching: surface
  (0.236337, -0.341177, 0.131959) m. This trial reused a far-view target:
  (0.261059, -0.322917, 0.129442) m, about 30.7 mm different laterally.
- Successful pilot lifted 23 cm over 12 simulated seconds; this trial requested
  only 5 cm over 4.267 seconds. Partial support clearance after the shorter lift
  cannot establish that the same grasp would fail a longer lift.
- Native cadence, closure duration and camera conditioning also differ.

Next integrated grasp qualification should refresh the grasp point after
approach, retain calibrated RGB-D provenance, and predeclare a lift sufficient
to test suspension with a bounded stop/review. Do not carry or insert on the
strength of the present partial-contact images, and do not repeat controller or
camera sweeps. No assembly/recovery phase is completed by this result.

The review builder now supports separate close/lift probes and checks that their
observation IDs are contiguous; raw precision receipts remain unmodified.
