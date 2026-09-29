# Guarded vertical retention continuation

The earlier guarded replay was mislabeled as a 23 cm lift. Its runner invocation
omitted `--lift-height`; the default is 5 cm. The declared sequence confirms a
5 cm lift from z=0.2332 m to z=0.2832 m. This explains why the carry reviews
still saw the card near its support.

From observation846, a separate guarded +18 cm probe preserved attitude and
gripper command. The 64-action limit was insufficient for the 0.0225 m/s ramp,
so it ended at observation910 with an explicit `local stage budget ended without
arrival` receipt; the hand was 84.350 mm short. Its image visibly shows the card
clear of the support, useful retention evidence but not a grasp certificate.

A separately declared +84 mm continuation executed six actions before the
native tracking guard returned `contact tracking guard stopped motion`. The
full-target endpoint error was84.947mm/0.0184rad; this is not a contact
measurement. The guard distinguishes this from an ambiguous simulator failure
and prevents automatic retry. Evaluator afterward remained
`success=false`, `score=0.33333334`. No carry, descent, release, or insertion
was issued.

This is the first native threshold-crossing guard result. It does not identify
whether the cause was collision, IK/PD stall, joint configuration, or another
controller issue. Preserve the state and investigate offline; do not push
farther from this worker. The probe wrapper now records budget-ended and
guard-stopped receipts as terminal `result.json` outcomes with
`no_automatic_retry=true` instead of an unhandled traceback.
