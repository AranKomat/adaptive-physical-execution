# Hybrid approach and failed-to-verify grasp

Episode `a8fa8c5ff0534f19b7819e1d52a1eca4`, original camera layout, FLUX DROID
gd-fp8r/native joint-position gripper conversion, Astra Flex medium. No privileged
policy inputs or cached motion recipe. This is not the sensor-target DiffIK pilot.

## What happened

`hybrid_clarified_20260930` used the clarified joint-vs-EEF prompt, horizon at most
32 and five reviews. Astra selected prefixes 32,16,8,8,8: 72 joint actions, 4.8 sim
seconds, 78.697 wall seconds, $0.485475. Final RGB shows the open gripper near the
card's upper edge. No grasp or native task success was verified.

An explicit continuation retained the SAME paused episode/observation at step 72.
The first continuation launcher stopped before any API call or action because
memory assumed an initial step zero. That bookkeeping issue was fixed without
renumbering observations or resetting the robot; the original budget-ended trace
was retained as clearly labeled continuation history, not a successful demo.

`hybrid_continue_fixed_20260930` executed two more 8-action prefixes. Fingers
closed and the hand then rose about 16 mm, but the card still appeared on its
support. On its third review Astra stopped for grasp-alignment inspection rather
than executing further closed-gripper transport. No software rejection/error,
no verified grasp/lift, native task success=false. Three calls cost $0.60369625;
continuation wall time 37.208 s, additional simulated time 1.067 s.

Combined: 88 actions / 5.867 sim seconds / eight paid calls / $1.08917125.
The two runner wall times exclude the paused development interval. The continuation
result's simulated_seconds field is cumulative episode time, NOT additional time.

## Interpretation

FLUX generated a plausible approach and attempted closure, so this is more than
an interface smoke test. It did not establish successful grasp geometry or task
competence. One stochastic episode is insufficient to rank checkpoints. The
reviewer avoided claiming a grasp from aperture alone and stopped after the
short lift test did not visibly move the card. Eight calls to reach this point
also remain above the desired one-to-few calls per meaningful stage.

Continuation history uses the existing reference-context encoding with an explicit
NOT-successful-demo label. Anchored LIVE memory begins at the preserved nonzero
step; the reviewer still mentioned a history gap despite supplied prior context.
This is not proof of seamless memory restoration or memory benefit. Tests cover
no reset, exact observation binding, default rejection of unsuccessful demos,
and exclusion of scorer data. Stopped/ambiguous episodes cannot use the new
budget-continuation path. No automatic budget extensions occur.

## Next decision

Do not simply lengthen closed-gripper transport or declare recovery. Inspect the
missed grasp geometry and whether visual evidence supports a failed-grasp diagnosis
and a bounded correction/reopen under the Hybrid gate. If evidence is insufficient,
retain that limit. Precision insertion remains a separate unresolved issue; the
camera branch's housing axis is not an insertion target.

Compact traces/results/images are in `docs/evidence/hybrid_clarified_20260930`
and `docs/evidence/hybrid_continue_fixed_20260930`. Full observations and simulator
recordings remain local. The temporary simulator was stopped after backup;
original simulator/FLUX services and unrelated workloads were left untouched.
