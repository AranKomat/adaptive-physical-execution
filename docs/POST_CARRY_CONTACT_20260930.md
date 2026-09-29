# Sensor-guided approach and first contact-intended attempt

## Result

The run advanced beyond elevated carry to two closer standoffs and one bounded
contact-intended descent. All 12 hand/camera endpoint checks passed, but final
native scene success was **false**, with grasp-held=true. The scene's `success()`
aliases its seating predicate. No release/retract or successful assembly is claimed.
Actual contact forces were not measured; reaching the requested hand pose is
not proof of correct connector engagement.

Run: `runs/post_carry_inspection_20260930`, episode
`d778fec65d80489fbc1e3ecc7ca4bc4f`. Compact evidence, commands and sampled video:
`docs/evidence/post_carry_inspection_20260930`.

This remains an operator-defined stage recipe with GPT visual reviews and native
DiffIK local feedback, NOT the FLUX hybrid or autonomous end-to-end task planning.
Initial grasp/carry pixel choices were explicitly reused on fresh depth in a
fixed fixture. Independent camera motion is idealized, without a collision body.
Grasp assistance is enabled; swept clearance remains unknown.

## What ran

1. Repeated fresh-depth approach, grasp/lift and elevated carry. An automated
   dispatcher replaced manual uploads between these already-qualified phases.
   Missing deployment of `plan_sensor_osc.py` stopped the first dispatcher before
   any command; it was copied and dispatch resumed in the SAME paused episode.
2. Moved the inspection camera while holding the card, then obtained one Astra
   review approving an 8 cm closer standoff. This left about 15 cm estimated
   vertical gap, conditional on no slip and a stationary socket.
3. Projected the tracked feature into current RGB-D: nearer surfaces occluded it
   in all three views. Moved the camera to the opposite side, without arm transit.
4. Astra identified a visible candidate gold contact edge at right pixel (350,168).
   That pixel failed depth continuity; the existing bounded refinement selected
   (350,167), with 9.808 mm local depth range. This is near the 10 mm rejection
   threshold, not high-precision confidence. No depth gate was relaxed.
5. The fresh point differed from the propagated one by +24.43 mm along the edge,
   -0.260 mm across it, and +2.215 mm vertically. Different locations along the
   strip are plausible; the discrepancy does NOT prove slip or identify a true
   midpoint. No longitudinal correction was made.
6. A separately scoped 9.5 cm standoff, with a declared minimum estimated gap
   of 5 cm, was reviewed and executed. It is not the earlier 12 cm gap condition.
   The estimated remaining gap was 54.81 mm; joint/orientation/depth stops stayed
   unchanged. Neither gap is a whole-object clearance certificate.
7. Astra reviewed and approved ONE explicit simulator contact trial: +2.297 mm
   cross-edge correction, 57.334 mm down, then hold and end. The intended feature
   target was 2 mm below the historical housing surface, not a known seat pose.
   No automatic release or search followed. Final hand target error was 1.960 mm,
   rotation error 0.01236 rad. Final evaluator: not seated, still held.

## Call and time accounting

Four new Astra Flex medium calls: standoff review $0.02019, fresh feature
localization $0.0197775, closer-standoff review $0.02534625, contact review
$0.0200025. Total **$0.08531625**. Earlier template-selection calls are not
included in this fresh-call total; do not claim this is the complete campaign cost.

4,678 native actions / 97.458 simulated seconds. Execution wall time summed over
phases was **470.418 s**, including capture, or 4.83x simulated time. Completed
command waits totaled **778.158 s**, including agent/operator work, transfers and
model reviews; not all waiting was model latency. Total wall time **1,250.107 s**.
The largest avoidable delay is paused orchestration, not a need for GPT at 48 Hz.
The video preserves simulated time, holds sampled RGB frames between captures,
and excludes waits with a visible label. It is not full-frame-rate recording.

## Interpretation and next step

Active camera movement provided a new visible contact-edge sample and allowed
progress to a contact-intended attempt with few model calls. This does not prove
improved task success, full object tracking, or calibrated insertion geometry.

The unresolved issue is correspondence/precision: housing surface vs insertion
gap, visible strip point vs connector center, and current orientation/bracket
alignment. A fresh point with nearly 10 mm depth spread and 24 mm along-edge
ambiguity is inadequate evidence for precise seating. Do not respond by pressing
farther, changing reasoning effort, or treating a hand-arrival pass as insertion.

Next obtain corresponding connector/slot axis or endpoint evidence, with a closer
or higher-detail independent view, and test one bounded alignment/recovery.
Preserve historical geometry as explicitly uncertain memory. Keep hidden seat
coordinates, object poses and grader predicates out of the control path. No
completed insertion/release, recovery, changed-layout transfer or FLUX execution
has yet been demonstrated. 144 CPU tests are software checks, not phase completion.
