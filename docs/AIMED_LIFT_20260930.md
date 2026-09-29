# Integrated lift and aimed inspection

## Predeclared protocol

Fresh worker with bounded gaze support from b9a4a75, same wrist-aim task,
rotation-integral controller and continuous transit as the successful smooth
lift. Cached pixel templates are remeasured on fresh legal depth at reset and
standoff. This is an operator-defined fixed-fixture assisted lift replay, not
autonomous discovery or recovery. Strict endpoint checks remain unchanged.

Preserve prior episode 13b72700c14b45ecaca1f7e32103ae78 at 885 before ending its
process. Selected depth/calibration, receipts and lift video are local; complete
recordings remain remote. Original simulator 8765 and FLUX 8766 are untouched.

Fresh worker PID 54862, remote 8767, process session 19989, tunnel session 14040.
Episode d3645c724ce046aeab7dbd48580af359 initialized at zero. An initial reset
attempt failed to connect to the local port; after restoring the tunnel, the
server explicitly reported `reset first`, establishing no episode had started.
Only then was initialization issued. No action/reset retry after ambiguity.

Replay approach to standoff, remeasure close target, then close and lift 23 cm.
Inspect retention before moving the idealized camera. Aim toward a legal
motherboard-region depth point, not a guessed socket coordinate.
Use bounded camera translation/aim with unchanged arm and grip. Review actual
socket and held-connector visibility before carry; no automatic insertion.

Initial measured target matches previous run:
[0.2610594815,-0.3229171756,0.1294422379] m from cached right pixel [364,258].

## Outcome

Approach reached standoff at observation 344 with strict arrival, 2.548 mm
position error. Close target on fresh depth matches the previous run:
[0.2747028421,-0.3371908051,0.1447898783] m, pixel [365,255] refined from
cached selection [365,256]. Grasp/lift execution is in progress.

Before camera execution: current oblique images do not expose the motherboard
surface. For this explicitly fixed-fixture test, use the previous episode's
legal measured region point [0.4526920775,0.0369339935,0.0321949074] only as an
inspection aim estimate. This is retained sensor geometry, not current socket
localization. Same-fixture reuse is an assumption; fresh images must establish
the useful view, and fresh feature depths must precede any carry. Planned eye
[0.60,-0.35,0.70] and interpolated aim pass translation/angular bounds in CPU
preflight. Arm/gripper hold, 64-action cap, no automatic retry. This differs
from the earlier occluded move only in aim; it does not certify camera clearance.

No assembly or recovery success claimed.

Lift finished at 693, strict final error 2.351 mm / 0.000134 rad; the left
image shows a suspended card and empty stand. First aimed camera move completed
at 757, 64 actions, 1.021 mm arm error, with orientation and eye readback passed.
The image is still gray: aim alone did not clear the occluding surface.
Next predeclared move: eye [0.60,0.05,1.00], same aim, 0.50 m over 64 actions
(0.1172 m/s). This moves above/toward the legally observed motherboard region
and away from the arm-side eye. Unknown clearance remains explicit; actual
image/readback and retention determine whether to proceed, no automatic carry.

Observation 821: second camera move passed, 1.019 mm arm error, motherboard now
clearly visible. Fresh Astra review selected `carry_above_slot`, held connector
left [146,151], socket right [314,190]. Measured surfaces respectively:
[0.2658604226,-0.3623102699,0.2695234038] and
[0.4722426527,0.0280299827,0.0375729090] m. Local depth spreads 7.343 mm and
0.538 mm; neither is calibrated localization uncertainty or clearance proof.

Predeclared carry: feature-relative translation plus 23 cm vertical standoff,
never lower hand. Resulting hand target [0.4810253831,0.0531425018,0.4634946883],
unchanged commanded quaternion [0,0,1,0], gripper command 0.3. Approximate
horizontal displacement 0.442 m. New same-episode carry runner splits transit
into <=6 cm chunks (at most 12 x 64 actions), settles only at the final endpoint,
and stops without retry on any nonarrival. No insertion/release; fresh visual
alignment review follows only if carry completes. Unknown swept clearance,
assistance and operator-defined phase structure remain explicit.

Carry completed at 1149: 328 actions / 21.867 sim seconds / 156.045 execution
seconds, strict final error 1.957 mm / 0.000433 rad. Targeting call $0.01939.
Fresh alignment review returned inspect: arm/case occlusion prevents identifying
both mating features. No descent or release.

Next predeclared inspection: eye [0.65,0.40,0.65], gaze [0.47224,0.02803,0.15],
64 holds, 0.4975 m from current eye. Gaze lies between measured socket position
and expected held-connector height; it is only a viewing hypothesis, not a new
physical target. This opposite-side oblique view seeks to avoid the arm-side
occlusion. Same held pose and grip, unknown camera/swept clearance, no retry.

## Final recorded state and interpretation

Opposite-side inspection completed at 1213, 64 actions / 31.451 wall seconds,
arm error 0.863 mm / 0.002103 rad. Camera eye [0.65,0.40,0.65], gaze
[0.47224,0.02803,0.15]. This exposes more motherboard and card body, but fresh
review again returned inspect: contact edge/key and matching socket alignment
remain unverified. No descent or release occurred. Preserve this held episode;
do not repeat the lift/carry merely to inspect it.

Current episode totals: 693 lift actions + 128 initial camera actions + 328 carry
actions + 64 final camera actions = 1213 actions. Lift execution wall time
311.978 seconds; carry 156.045 seconds. Three Astra Flex medium reviews cost
$0.01939 + $0.0191525 + $0.02469 = $0.0632325. Shared reserved calls now 4361;
recheck the private ledger before further requests; unresolved holds remain.

This qualifies the bounded gaze-control path and a fresh sensor-feature-relative
carry in the integrated worker. It does not establish reliable mating geometry,
insertion, release, full assembly, autonomous discovery or recovery. The new
same-episode carry runner is intentionally restricted to elevated translation;
197 CPU tests pass, including stale target, descent, rotation and release rejects.

Next separate feature localization from joint alignment certification: obtain
the connector edge and socket axis from actual visible surfaces, maintaining
observation provenance and uncertainty. Do not require a visible key merely to
localize a rough axis, but do not equate rough localization with insertion
permission. Avoid more blind camera sweeps or lowering to a guessed target.

Evidence under `docs/evidence/aimed_lift_20260930/`: aimed motherboard image,
held/carried card images, mating view, fresh carry selection and measured plan,
final receipt and negative mating review. Full left control-latch video is
`lift_carry_1x.mp4`, 1x simulated time, model waits excluded, assistance labeled.
Selected RGB-D/logs and full left frames are local. Complete depth recordings
remain on the host; a Git push is not a complete raw-data backup.
