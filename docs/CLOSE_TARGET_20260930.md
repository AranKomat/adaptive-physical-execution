# Close-range grasp refresh

## Predeclared protocol

Fresh episode, wrist-aim task and angular-integral worker unchanged from the
previous contact trial. Operator-defined approach uses the earlier far-view
pixel template on fresh depth ONLY for standoff. Then obtain one fresh Astra
grasp target from current camera images and measured depth before descending.
Inspect the selected surface and reject invalid depth or an inspect response.

The bounded continuation is open descent, closure, then a 23 cm vertical lift,
subdivided into at most 6 cm targets with 64 actions each. No carry or insertion
without subsequent visual evidence of suspension. Strict descent arrival remains
required; closure/lift use the already declared 10 mm / 0.15 rad exploratory
completion bounds. Hard worker abort checks remain unchanged. Stop on failure,
no automatic retry. Unknown clearance and enabled simulator grasp assistance
remain disclosed; this is not an autonomous recovery or hardware-safe plan.

This tests an integrated close-range-targeting recipe, not a clean ablation:
target refresh, lift height and action budget differ from the last trial.
No hidden object state is supplied to control or target selection.

## Outcome

Fresh episode `c3145c96f5344d6fa999b5b506de89ae` completed seven open approach
stages / 448 actions and paused at standoff. All strict arrival checks passed;
final error 1.933 mm / 0.000151 rad. Zero paid calls. No descent, closure or
lift was issued. Fresh target selection and suspension qualification remain
pending while the requested project handoff is prepared.
