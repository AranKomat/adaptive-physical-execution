# Research Handoff: Assisted Grasp, Carry, and Coarse Alignment

Date: September 30, 2026 (JST).
Repository: https://github.com/AranKomat/adaptive-physical-execution
Experiment/code cutoff: `81a8134` on `main`.

This is a self-contained update since the broad
[shared-local-execution handoff](RESEARCH_HANDOFF_LOCAL_EXECUTION_20260930.md).
It consolidates subsequent aperture, geometry, camera, carry, and alignment
experiments. No new robot experiments or paid calls were run to write this
report. Live-state references below mean **last recorded**, not freshly checked.

## Bottom Line

We now have a concrete sensor-guided, assisted GPU grasp/lift, a 43.2 cm carry,
and two reviewed coarse positioning steps above the motherboard. The card
remained visibly held through the last recorded observation. We identified a
real grasp-target geometry bug and demonstrated a matched aperture effect.

**We have not installed or released the card successfully.** We have not shown
autonomous recovery or run the fair enhanced Direct-A/Direct-B/FLUX+GPT comparison.
These successes are operator-mediated local DiffIK execution with Astra reviews,
not a FLUX Hybrid success or a fully autonomous task solution.

The bottleneck has shifted from obtaining a retained lift to resolving and
executing mating geometry, with substantial simulator wall-time overhead still
present. Progress is useful, but repeated inspection and diagnostics remain too
expensive relative to the goal of an integrated demonstration.

## Project and Experimental Conditions

The project studies adaptive execution in the EmbodiedSWE/RoboBench PC-assembly
simulator, using a Franka Panda. GPU installation is the priority; RAM is
suspended. We want a few model decisions per meaningful physical stage, fast
local execution, and eventual comparisons of execution memory and recovery.

- Model in this interval: GPT-6 Astra Flex, medium reasoning.
- Robot motion: calibrated RGB-D targets and robot FK compiled into guarded local
  differential IK trajectories. The model is not called for every control step.
- Operator involvement: recipe construction, mode selection, visual review, and
  deciding which bounded experiment to execute. Do not label this autonomous.
- Legal control inputs: RGB-D, camera calibration, robot proprioception/FK,
  historical evidence with provenance, and execution receipts.
- Excluded from control: privileged object poses, hidden collision truth,
  grasp/latch state, and native evaluator feedback.
- Native grasp assistance/weld is **ON**. Retention is not proof of ordinary
  frictional grasp quality or real-robot transfer.
- An independent movable inspection camera was added in a fresh episode. It is
  idealized and has no collision body: this is augmented sensing, not the original
  fixed-camera baseline or a hardware-qualified camera mechanism.
- Depth is an idealized simulator sensor. Plane intersections are labeled inferred
  geometry rather than disguised as measured gap or seating depth.
- Tracking/abort guards remain active. No automatic retry follows ambiguous
  execution or a guard stop. Unrelated workers/CPU workloads must remain untouched.

## Concrete Results Since the Previous Report

### 1. Matched Aperture Test: Positive, With an Assistance Confound

Two fresh seed-0 episodes used the same approach, sensing, controller, closure
budget, and lift compilation rule; only commanded closure/hold aperture changed.
No paid model calls were needed for this comparison.

| Commanded aperture | Final hand error | Hand rise | Visual outcome |
| --- | --- | --- | --- |
| 0.3 | 4.573 mm | 225.7 mm | GPU retained and lifted clear of support |
| 0.0 | 0.172 mm | 230.5 mm | Hand lifted, GPU stayed on support |

This establishes an aperture contributor in this fixture, not the explanation
for every earlier Direct failure. Assistance eligibility depends on aperture,
stall/proximity conditions, and debounce; the test does not isolate weld
eligibility from physical contact mechanics. Do not silently override model
closure commands to 0.3. Give future compared methods the same labeled evidence.

The old generic 3 mm endpoint threshold incorrectly conflated hand precision
with useful lift success. A prospectively declared upward-lift criterion of
10 mm / 0.03 rad now supplements visual retention; original strict receipts
remain intact. This does not loosen insertion tolerances or tracking stop guards.

Source: [aperture result](APERTURE_PAIR_RESULT_20260930.md).

### 2. Experience Transfer and an Actual Surface-Selection Bug

Astra explicitly selected aperture 0.3 after receiving the comparison evidence.
However, the nearest smooth depth patch could land on a vertical side face rather
than the intended top face. Within the same two-pixel search:

- Side patch `[372,261]`: normal/up cosine 0.08879, height 0.129346 m.
- Top patch `[373,258]`: cosine 0.99652, height 0.143871 m.

Both were locally smooth. The wrong face changed grasp height by about 14.5 mm.
We added a nine-point calibrated plane measurement and an opt-in upward-surface
requirement: within 45 degrees of world-up, plane RMS at most 1 mm, unchanged
two-pixel search radius. This is geometry refinement, not object identity or
collision certification.

The fresh selected region/aperture plus refined face and operator-reviewed local
sequence produced a retained lift: 84 descent, 64 closure, and 181 lift actions;
final hand error 4.557 mm. Four calls across the preceding inspection/regrasp
continuation cost $0.13304125, with 480 actions / 32 simulated seconds overall.
The intervention combines experience, inspection, and refinement, so their
individual benefits are not isolated.

Source: [upward-surface grasp](UPWARD_SURFACE_GRASP_RESULT_20260930.md).

### 3. Fresh Augmented-Sensor Replay and 43.2 cm Carry

The old worker did not support the new camera. Its terminal RGB-D and command
journals were backed up before retiring only that worker. A fresh same-task/seed
episode enabled independent inspection sensing and replayed the operator recipe
against fresh legal depth: 330 approach, 64 closure, and 181 lift actions.
The GPU was visibly retained at step 575.

An initial inspection view was occluded by the arm; a vertical look-at proposal
was rejected before execution for a singularity. A high-oblique camera position
exposed the motherboard. Astra selected fresh card/socket regions, and the local
controller executed a **43.2 cm horizontal carry**:

- 320 actions / 21.333 simulated seconds / 149.747 worker wall seconds.
- Final hand error 0.859 mm / 0.000421 rad.
- Eight transit waypoints passed without intermediate settling pauses.
- GPU visibly retained; mating features remained occluded afterward.

A subsequent model-selected camera path failed angular-rate preflight and was
not executed. This was a successful carry, not installation or a loaded-fast
motion qualification.

Source: [camera and carry](HEAD_CAMERA_CARRY_20260930.md).

### 4. Retiming and Closer Standoff: Motion Passed, Geometry Still Incomplete

Splitting the selected camera path into two 64-action legs reduced peak angular
rate from 0.37775 to 0.18902 rad/s under the unchanged 0.35 rad/s limit. Both legs
arrived. A reviewed 8 cm closer card standoff also arrived: 91 actions, 6.067
simulated / 43.242 wall seconds, 1.543 mm endpoint error.

Earlier depth propagated with current FK under an explicitly unverified no-slip
assumption predicted about 15 cm remaining separation. This was not clearance.
An opposite-side camera exposed PCB and partial socket housing, but not the gold
connector. Two housing samples were not sufficient to define the mating line.

Source: [standoff and retiming](HEAD_CAMERA_STANDOFF_20260930.md).

### 5. Lower Camera Resolved Connector Visibility; Exact Rail Tests Were Negative

Three 64-action camera moves exposed the gold strip/key and CPU-adjacent socket.
At step 1498, four 3x3 depth samples passed with 1.62-2.16 mm spread. Sampled
connector/socket-rim axes differed by 2.338 degrees, with a minimum sampled
vertical separation of 132.801 mm.

Those points were not corresponding longitudinal endpoints; a socket rim is not
its channel centerline. Opposing-rail identification declined at both broader
and closer views. An opt-in single-pixel rail diagnostic also declined, showing
that the 3x3 depth filter alone did not explain the failure. We added measured
geometry feedback to reduce silent socket switching. No insertion was attempted.

Source: [low-view geometry](LOW_VIEW_GEOMETRY_20260930.md).

### 6. Reviewed Coarse Approach and Inferred-Line Lateral Alignment

Exact opposing rails were unnecessary for another bounded, noncontact approach.
Four fresh surface anchors supported one reviewed **4 cm descent** with at least
8 cm nominal sampled separation, preserved attitude/aperture, and existing guards.
This exploratory mode is separate from strict contact modes, not a clearance proof.

- Steps 1562-1626: 64 actions, 4.267 simulated / 29.547 wall seconds;
  1.704 mm / 0.001453 rad final error.

At 1626, three model-selected channel-center pixels were intersected with a
current measured housing plane. Results are explicitly `inferred_point_world_m`.
The helper requires matching observation IDs, plane RMS <=1 mm, extrapolation
<=15 cm, and rejects grazing/behind-camera rays. The inferred plane is not the
gap floor or seating depth.

One gold-strip point passed depth validation; the second failed a discontinuity
check and was excluded. The single valid point supported only a transverse
correction of **12.616 mm**, at unchanged height, attitude, and aperture 0.3.

- Steps 1626-1690: 64 actions, 4.267 simulated / 29.694 wall seconds;
  0.696 mm / 0.001592 rad final error.
- GPU remained visibly held. No contact, insertion, or release.
- One-point lateral alignment does not establish longitudinal/key or full angular
  alignment. Nominal sampled separation before correction was 89.723 mm.

Source: [coarse alignment](COARSE_ALIGNMENT_20260930.md).

## Software and Verification

Relevant additions include measured surface-plane selection, observation-aware
plane projection, explicit coarse-approach proposals/review, single-pixel rail
diagnostics, and neutral manipulation reviews that do not presuppose contact
failure. Key implementation locations:

- `src/physical_exec/depth.py`: `surface_patch`, `project_pixel_to_surface_plane`.
- `src/physical_exec/carry.py`: `coarse_approach_stage`.
- `scripts/plan_sensor_osc.py`: explicit upward-surface selection.
- `scripts/prepare_manipulation_review.py`, `prepare_coarse_approach_review.py`.
- `scripts/prepare_sensor_target_request.py`: geometry/centerline review modes.
- `scripts/run_sensor_carry.py`: reviewed coarse-approach execution.

Last recorded software verification: **378 CPU tests passed** at the experiment
cutoff. These include provenance, unsupported-geometry rejection, and inferred
plane tests. Tests were not rerun for this documentation-only update. Passing
component tests are not physical task completion or hardware qualification.

## Status and Fair-Comparison Limits

| Workstream | Status at cutoff |
| --- | --- |
| Shared local EEF execution | Implemented; operator-reviewed physical stages exercised |
| Aperture contribution | Matched positive result, assistance mechanism unresolved |
| Sensor-guided grasp/lift | Positive assisted result and fresh-episode replay |
| Loaded carry | Positive 43.2 cm conservative carry; fast loaded transport unqualified |
| Active inspection | Useful augmented views; original fixed-camera condition not solved |
| Socket positioning | Coarse approach and one-point lateral correction only |
| GPU installation/release | Not achieved |
| Autonomous integrated task | Not achieved |
| Recovery | Earlier attempts unsuccessful; no new successful recovery |
| Enhanced Direct-A/B/FLUX+GPT comparison | Still pending under matched current conditions |
| Execution-memory comparisons | Still pending meaningful integrated baseline |
| RAM | Suspended; no verified installation |

Historical Direct-A medium used 23 calls / 90 actions; Direct-B medium 20 / 58;
Direct-A high 20 / 71. None verified a lift; native scores were zero. Short FLUX
trials also did not verify a grasp. An earlier reviewed DiffIK recipe lifted and
carried, but release tipped the GPU onto the motherboard; native success was
false, score about 0.3333, and recovery failed.

These precede the aperture, geometry, camera, and execution improvements. They
are not fair evidence that the current recipe/model is superior. No end-to-end
phase should be marked complete on the strength of the new positioning tests.

## Efficiency, Costs, and Remaining Bottlenecks

The documented regrasp-through-alignment groups used **18 paid calls totaling
$0.65778875**: regrasp $0.13304125; camera/carry $0.11855125; retiming/standoff
$0.0822175; lower-view geometry $0.18956875; coarse alignment $0.13441.
This is a scoped subtotal, not all-project spend, and excludes the no-API aperture
pair. Shared reservation count was 4510, ceiling $85, unresolved holds retained;
that shared count is not this project's model-call total.

One carry used a model-selected destination followed by hundreds of local actions,
so GPT is no longer required for every few millimeters. But the overall sequence
still needed multiple inspections and operator interventions. We have not yet
demonstrated the desired few-call autonomous high-level action pipeline.

Worker execution remained roughly **7x slower than simulated time**: the carry
took 149.747 wall seconds for 21.333 simulated seconds; the latest two stages
took 59.240 wall seconds for 8.533 simulated seconds. This excludes additional
model/operator time. Simulator/rendering/depth/controller overhead matters;
GPT latency alone does not explain the slow videos.

Earlier unloaded 5x feedforward up/return reduced total simulated duration from
13.933 to 4.533 seconds (3.07x realized gain). A 10x test stopped under its guard.
There is still no qualified 5-10x loaded carry, fast contact, or task speedup.
Use the eligible fast-open-transit configuration, but do not extend unloaded
qualification to closed-grip transport without evidence.

Other limitations: partial occlusion, possible target/socket misassociation,
unverified no-slip propagation, plane extrapolation accuracy, insufficient key/
longitudinal geometry, simulator grasp assistance, and operator involvement.
Calibration fixes improved behavior; they did not remove those limitations.

## Last Recorded State and Evidence

- SSH: `ssh -p 45579 root@76.71.203.193`.
- Remote repo: `/workspace/adaptive-physical-execution`.
- Remote Python: `upstream/EmbodiedSWE/.venv/bin/python`.
- Last recorded worker: PID 103000, port 8772.
- Episode: `5fc1330e1fb9410e9cc56d5c948ee0af:1690`.
- Card visibly held above motherboard, aperture 0.3; no insertion/release in this
  fresh episode. Do not assume the process or physics state is still live.
- Local terminal RGB-D/calibration: `runs/gpu_head1690_flat`.
- Local lateral receipt/plan: `runs/gpu_head1626_lateral/00_receipt.json`,
  `runs/gpu_head1626_lateral_plan.json`.
- Geometry: `runs/gpu_head1626_centerline_measurements.json`,
  `runs/gpu_head1626_socket_plane.json`.
- Remote full recordings: `runs/gpu_head_enabled_20260930/recordings`.

Public evidence folders under `docs/evidence/`: `aperture_pair_20260930`,
`upward_surface_grasp_20260930`, `head_camera_carry_20260930`,
`head_camera_standoff_20260930`, `low_view_geometry_20260930`, and
`coarse_alignment_20260930`. These hold selected requests, receipts, plans,
images, and reviews. Local critical backups are not a claim that every full
per-step remote recording has been downloaded.

## Prioritized Next Experiments

1. Read current worker identity/state without mutation; obtain fresh observations
   and confirm retention before any continuation. Never replay stale world targets
   or reset a held scene just to reproduce this report.
2. Resolve current connector/key and longitudinal placement using legal sensing.
   Treat the inferred housing-plane line as a coarse hypothesis, not seating depth.
   Define a bounded continuation with explicit abort and recovery behavior.
3. Attempt an integrated approach/contact/installation only when the proposal has
   adequate task-specific geometry. Verify release and independently score the
   physical outcome afterward; do not feed evaluator truth into control.
4. Run enhanced Direct-A, Direct-B, and FLUX+GPT with the same cameras, aperture
   experience, depth semantics, local controller, assistance, seeds, budgets, and
   success criteria. Label augmented sensing separately from fixed-camera results.
5. After a useful integrated baseline, test a predefined recovery and execution
   memory variants. Measure calls per meaningful action, sim/wall duration, and
   independent task outcome, not merely endpoint precision.
6. Profile simulator/render/depth overhead and qualify faster loaded motion
   separately. Do not weaken stop guards to obtain a faster video.

Do not return to aperture sweeps, rail-wording sweeps, checkpoint searches, or
optimizing a harmless 4.6 mm lift residual. The next valuable result is a useful
integrated physical effect at the socket, not another isolated tiny movement.
If sensing still cannot support that continuation, record the specific missing
geometry and choose an explicit change of experimental condition rather than
silently treating unknown space or inferred geometry as certified evidence.
