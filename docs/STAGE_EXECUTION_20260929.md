# Stage-level execution priority

User direction supersedes continued long GPT-Direct sweeps. Direct remains a
bounded recovery/reference option, not the main execution strategy. Native task
success, recovery and experience reuse remain the objective; this does not replace
them with a smaller motion-only goal.

## Next sequence

- [x] Capture idealized RGB-D and calibrated camera poses without object-state queries.
- [x] Add strict visible-surface deprojection, rejecting invalid/mixed neighborhoods.
- [ ] Verify spatial agreement across views and robot geometry before control use.
  Cross-view capture audit now passes a coarse consistency check after correcting
  stale wrist-camera pose metadata; see `SPATIAL_GROUNDING_20260929.md`.
- [ ] Establish robot-only finger geometry; do not mistake the hand origin for contact.
- [ ] One sensor-grounded approach with local feedback, action/time bounds, progress
  checks and termination on rejection or unexpected changes. Keep execution receipts.
- [ ] Inspect arrival once, then attempt grasp/lift and independently verify effect.
- [ ] Qualify FLUX before using it as an alternative local executor. Reviewing every
  short FLUX chunk with GPT is not sufficient to meet the call-efficiency objective.
- [ ] Continue alignment/insertion, recovery and successful-trace reuse after capture.

Target: one to a few GPT calls per uncomplicated stage (approach, grasp/lift,
alignment/insertion). Report actual calls, executed actions, simulated/wall time,
cost and physical stage completion. A lower call count without progress is failure.
Do not silently lengthen open-loop sequences, relax limits, or claim collision
safety from target-point depth. Local monitoring must run between bounded chunks.

## Measurement evidence and limits

On the retained capture, the measured hand frame projects to approximately
(94.46, 3.56) in the left image, consistent with its visible location. This is a
coarse visual sanity check, not independent quantitative calibration validation.

An operator-selected card-surface pixel (158,216) in the original 640x360 left
image deprojects to world (0.260935,-0.358056,0.099727) m. Optical depth is
1.256487 m and the 5x5 neighborhood range is 0.017708 m. Identity selection was
manual visual inspection, not autonomous model discovery. No object transform
or semantic simulator ID was used. This is a visible surface point, NOT a grasp
center, obstacle-free waypoint, or measured statistical confidence interval.
No motion was commanded from it. The helper keeps observation identity attached.

112 CPU tests pass. They establish software checks, not successful approach,
calibration accuracy or manipulation. No additional API calls were made.

## First local-feedback approach

`runs/local_approach_20260929` continued the freshly captured, corrected-depth
episode with an exact observation-ID check. The operator-selected card surface
pixel (158,216) defined a hand target 0.30 m above that surface along world z.
This explicit standoff is a probe parameter, not learned grasp geometry.
The local controller preserved orientation and commanded an open gripper,
replanning a single at-most-1-cm step from measured hand position each time.
Existing IK, joint continuity and command limits remained active.

It executed 60 actions in 37.62 wall seconds (4 simulated seconds), with zero
GPT calls and no command rejection. Target distance decreased:

| Control steps | Hand-target distance |
|---:|---:|
| 0 | 196.39 mm |
| 10 | 168.37 mm |
| 20 | 140.11 mm |
| 30 | 111.76 mm |
| 40 | 83.46 mm |
| 50 | 55.16 mm |
| 60 | 26.73 mm |

Result: action-budget termination, NOT arrival (3 mm criterion), grasp or task
success. It made steady progress without GPT per-step corrections. Target selection
was manual, so zero calls must not be presented as an autonomous perception result.
The result file from this first run lacks an explicit stop-reason field; 60 actions
and the fixed cap establish termination. The script now writes that field.

This exploratory simulator probe does not certify swept-volume clearance or
detect arbitrary scene changes. Its local monitoring covers measured progress,
execution receipts and budgets, not a general visual event detector. Do not deploy
it on hardware or represent it as a production stage executor. Next: bounded
arrival completion and inspection, then grasp geometry/attempt; do not restart
long GPT-Direct loops just to finish this transit.

## Verified standoff arrival

`runs/local_approach_settle_20260929` explicitly continued the same episode from
observation `3cff69ee0d184428a33eb0af51fd1937:60`, preserving the target and all
motion limits. The extension requires the previous run to have ended unambiguously
at its 60-action cap and requires exact current observation identity; it is not
an automatic retry after an unknown execution result.

Arrival succeeded after 10 additional actions, at observation step 70: measured
hand-target error 2.356 mm, below the unchanged 3 mm criterion. Extension wall
time was 6.523 s. Combined transit: 70 actions, 4.667 simulated seconds, 44.148 s
execution wall time excluding operator pause, zero GPT calls. No resets occurred.
The inspected final left RGB image shows the open hand above the supported card.

This completes the bounded manual-target standoff approach probe, not autonomous
approach selection or manipulation. The conservative 0.30 m surface-to-hand
offset is not a grasp-ready pose. Grasp placement/orientation, physical capture,
task success, and stage-level model selection remain unverified. The continuation
trace (including RGB replies) is backed up locally. 112 CPU tests still pass.

## Closer approach and first local grasp attempt

Fresh wrist depth at step 70 and visually selected pixel (253,130) gave surface
point (0.247853,-0.331487,0.144153) m, with 0.135 mm local depth range. Two
additional surface samples along the visible edge differed by approximately
(-0.096655,-0.000013,-0.000056) m: the long edge runs along world X. The hand
orientation closes the fingers along world Y. This supports the closing-axis
choice, not the contact-center placement or a guaranteed grasp.

`local_pregrasp_20260929` used that fresh surface point with a declared 0.13 m
world-z hand standoff. It arrived within 2.423 mm after 47 actions / 29.70 s wall,
without GPT calls or reset. The left view showed open fingers near the card top.

`local_grasp_lift_20260929` then tested an operator-designed sequence: descend
35 mm while open, close for 12 actions, and lift to 25 mm above the starting hand
height. Each transit used measured-state corrections capped at 7 mm and required
3 mm arrival before proceeding. Existing simulator limits remained unchanged.
It executed 59 actions in 39.18 s wall, with no errors or GPT calls. Closure ended
at open fraction 0.1492; after lift it was 0.0030. Final left RGB at step 176 shows
the card still on its support. Thus **grasp/lift failed**, despite successful robot
pose execution. No native task success or successful recovery is claimed.

This is a manual sensor-grounded local-control diagnostic, not FLUX performance
or an autonomous GPT stage selection. Grasp-weld assistance remains enabled as in
the baseline. The kinematics-only URDF does not include finger collision geometry;
an attempted standalone USD inspection lacked the pxr runtime, so exact fingertip
contact geometry is still unverified. Next correction should address observed
contact placement, not reasoning level or more per-step GPT calls.

## Deeper recovery probe

Robot-only USD inspection succeeded by loading the bundled USD Python runtime
with its library paths (no new package/system changes). The left-finger mesh
local z extent is 0.000133..0.053900 m. Together with the 0.0584 m finger-joint
origin, its extreme tip is approximately 0.1123 m from the hand frame. This is
a visual mesh extent, NOT a qualified friction/contact-pad center or collision
model. Previous closure hand z=0.242679 m put that tip around z=0.1304 m,
only approximately 14 mm below the selected top surface at z=0.144153 m.

`local_deeper_grasp_20260929` continued at step 176 with explicit reopen,
80 mm descent relative to that post-lift hand pose, 12 close actions and a bounded
lift. It executed 104 actions in 67.69 s with zero GPT calls. Descend completed
at step 228, closure at step 240 (open fraction 0.15838), and lift exhausted its
40-action budget at step 280. The hand remained 77.09 mm from the lift target;
final open fraction was 0.11983. No automatic retry or further lift was issued.

Final left RGB shows the card tilted relative to its original supported pose:
this is visible object displacement, but NOT a verified secure grasp or lift.
The hand also shifted laterally under attempted lifting. Whether this represents
snagging, constrained contact, slip or grasp-assist behavior is not resolved by
the frame. Do not extend upward motion blindly or claim a successful recovery.
The next decision needs current multi-view/contact evidence, not another depth
increment. Baseline grasp assistance remains enabled; no physics gains changed.

## One-call stage review

`astra_stage_review_20260929` submitted the three retained step-280 RGB views,
robot public state and the prior local-execution outcome to Astra Flex at medium
reasoning through the authorized pinned OpenAI Flex route. No object poses,
grader scores or privileged contact data entered the request. The explicit prompt
included the operator's observed tilt and failed-capture context; this is a
context-informed review, not a blind perception benchmark.

One call cost $0.01565875 (1,852 total reported tokens). JSON-object output was
requested, then strictly parsed into one of `reopen_hold`, `inspect`, or `stop`.
The model selected `inspect`: the left view suggests a nearby support, but the
wrist is occluded and the right view does not establish load-bearing support.
It recommended no further lift and no release until support is established.
No motion was issued from this recommendation. The review and raw API evidence
are retained locally; the shared ledger retains all previous holds.

This demonstrates a cheap stage-boundary review, not successful recovery,
autonomous grasp planning or lower cost per completed task. The constrained menu
does not test arbitrary high-level planning. Current observation lacks force or
contact sensing; no configured Franka contact sensor was found in its robot source.
Repeatedly asking about the same occluded images is unlikely to add evidence.
Next work should obtain a genuinely informative legal view/contact measurement
or evaluate the motor-policy route, rather than force/release by guesswork.
117 CPU tests pass, including stage-output validation; task success remains open.
