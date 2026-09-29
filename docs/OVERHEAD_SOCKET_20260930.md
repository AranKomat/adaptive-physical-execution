# Overhead socket localization and stage-feedback trial

## What this condition is

This is GPT visual target selection plus legal RGB-D and deterministic native
DiffIK feedback, with operator-defined grasp/lift/carry phases. It is neither
the original per-chunk GPT-Direct baseline nor the FLUX+GPT hybrid. FLUX does
not control these actions. Grasp assistance remains on and clearance unknown.

The previous controlled carry succeeded mechanically but two post-carry reviews
could not identify mating features. Initial images also showed case-rim
occlusion. This follow-up changes the right external camera only: eye moves
from (0.15,0.95,0.85) to (0.45,0.5,1.4) m, retaining the original generic workcell
target (0.45,0,0.1), focal length 18, and 640x360 image size. Left/wrist views,
task physics, robot, controller and action bounds remain unchanged. Camera
coordinates are operator configuration, not simulator object-pose queries.
Do not pool this condition with earlier camera-layout trials as matched trials.

Configuration: `configs/tasks/pc_gpu_overhead.json`.
Run: `runs/sensor_overhead_20260930`, episode
`50eea9d3b33f45269569bfa048228c91`.

## Evidence so far

Before motion, one Astra Flex medium call localized the socket housing and its
long axis in the right image, explicitly not its insertion gap/key. Cost $0.02399.
Center (311,193) passed the existing 3x3 depth continuity check: surface world
(0.473576,0.014824,0.043678) m, depth range 1.996 mm. One endpoint (282,193)
failed the same check. A one-pixel inward diagnostic passed, but the other
endpoint lies 6.79 mm lower than center, so this is not a qualified precise
socket pose. No motion was issued from that three-point estimate.

The unchanged template-based approach and grasp/lift sequence repeated the
previous endpoint errors exactly through action 1984: controlled assisted lift
within 1.945 mm / 0.020941 rad. Left/wrist pixel templates are declared reuse,
not fresh autonomous grasp discovery. The new overhead image exposes the socket
while the card is still held off to the side.

A fresh carry review selected held pixel left (151,155) and socket pixel right
(307,194). Both passed 3x3 depth checks; the measured socket surface is
(0.484030,0.017603,0.043678) m. The two independently selected socket centers
differ by about 11 mm, illustrating coarse rather than insertion precision.
An elevated three-waypoint carry completed with 23 cm feature standoff and
no descending hand motion. Final endpoint error was 1.714 mm / 0.018215 rad.

## Outcome

At action 3193 the gripper/card obscured the mating interface in the overhead
view; the wrist view exposed CPU/RAM but not the relevant connector pair. The
current-images-only alignment review requested inspection. A follow-up supplied
the same-episode pre-grasp socket image and its earlier selection, explicitly
labeled historical rather than current clearance. This fixed the loss of target
history in the review: the model acknowledged the previously observed socket,
but still could not verify current alignment or key geometry. It again requested
inspection. This is not evidence that memory is useless, nor a physical memory
benefit result; the prompt still asks for explicit connector/key correspondence.

The episode ended with a zero-motion finish command. Total 3,193 actions /
66.521 simulated seconds / 736.370 wall seconds including pauses. Four new Astra
Flex medium calls cost $0.09081625; earlier grasp pixel templates were reused.
Post-control evaluator: held=true, scene_success=false. No descent/insertion,
release or recovery was attempted. Full trace is retained locally; compact
evidence and before/after camera images are in `docs/evidence/sensor_overhead_20260930`.

Next sensing option, discussed with the user: a bounded independent inspection
camera with translation as well as pan/tilt, rather than moving the grasp just
to move the wrist view. A movable rig is NOT implemented in this commit. In
simulation it must be a declared sensing condition, with admissible viewpoints,
movement time and fresh extrinsics; no teleportation through geometry. Do not
claim real-hardware feasibility/cost or safety from a virtual camera test.

135 CPU tests pass, including rejection of cross-episode, future or mismatched
historical selections. These do not constitute a completed manipulation phase.

## Why the video looks slow

Translation ramp is explicitly capped at 0.0225 m/s. Phases have fixed durations
and include settling/holding; completion is not yet early-terminated on stable
arrival. Native control is 48 Hz, not one GPT call per control step. Sampled
videos preserve simulated time and exclude model/operator waits. The previous
65.208-second video came from 1,116.920 wall seconds including pauses, transfer,
inspection and simulation execution; it cannot establish a pure controller
runtime or model-latency breakdown.

Future pilot runs now record completed command-wait time and per-phase execution
wall time (including capture), plus actual camera layout. The running episode
predates this instrumentation. No speedup claim is made. First establish useful
insertion; then test faster ramps and early stable-arrival termination explicitly.
