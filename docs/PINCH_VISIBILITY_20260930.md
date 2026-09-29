# Nominal pinch-center visibility

Retained grasp-attempt observations 72,80,88 in episode
`a8fa8c5ff0534f19b7819e1d52a1eca4` were audited using measured hand pose and
the corresponding calibrated camera transforms. No object pose or evaluator
input is used. `scripts/audit_pinch_projection.py` reproduces the calculation;
output is `docs/evidence/hybrid_continue_fixed_20260930/pinch_projection.json`.

The nominal pad center is hand-local [0,0,0.1034] m, following pinned upstream
`rl/robobench_rl/tasks/common.py`'s robot convention. This is static robot
geometry, not a scene-derived target or actual contact measurement.

All three wrist projections are approximately (224.84,-41.25), outside the
640x360 image. Because this camera is attached to the hand, that location stays
essentially fixed. A card looking large in this wrist view does not show that
it lies between the pads. The left-view projections are (160.04,173.50),
(161.91,177.14), and (168.98,167.30). Visual comparison is consistent with the
pinch center above the card rather than an established grasp, but no exact
target-relative 3D gap is claimed from these projections alone.

Added nominal pinch world XYZ and its hand-local offset to reviewer context
only for robot=franka/frame=panda_hand. It is explicitly not contact evidence.
No target state, policy weights, motion bounds, or camera configuration changed.
The subsequent live trial tests whether this extra robot geometry helps;
the offline audit itself does not establish improved performance.

## Live follow-up

`hybrid_pinch_20260930`, episode `6f09afb672af47bfb571208d16d8f8a2`, used an
eight-review/256-action cap with uninterrupted memory. Actual execution stopped
after two 16-action prefixes and three reviews: 32 actions, 2.133 sim seconds,
47.460 wall seconds, $0.22412125. No grasp, correction, or task success occurred;
there were no software rejections or errors. Full records are backed up locally,
with compact evidence in `docs/evidence/hybrid_pinch_20260930`.

The reviewer explicitly obeyed the earlier added rule to stop after two chunks
whose progress was unassessable. That rule conflated uncertainty during approach
with observed no progress and curtailed this experiment before a grasp attempt.
Removed the fixed count, while retaining bounded budgets, actual action validation,
stops for concerning motion/repeated observable no progress, and the warning not
to transport based on an unverified grasp. This returns uncertainty handling
closer to the original Hybrid self-correction intent. The revised rule has not yet
been live-tested. No claim that pinch context helps or harms task success is justified.
