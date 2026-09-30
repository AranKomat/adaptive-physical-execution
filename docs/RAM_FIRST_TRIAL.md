# RAM: next independent assembly experiment

## Controller qualification ready; GPU capacity/scene retention decision pending

Prepared `probe_local_stage_service.py --ramp-return-qualification
--contact-tracking-guard`: fresh worker only, open hand, fixed orientation,
12cm upward excursion and return in four bounded segments, max256actions.
Robot-only endpoint IK preflight precedes motion; unchanged tracking guards,
continuous intermediate transit and strict phase-end arrival. No object contact
intended or model calls. Requires worker metadata advertising the new anti-windup
implementation; old workers are rejected before reset.265tests pass. This is
prepared, NOT a completed physical qualification or task result.

All six workers still run. GPU process allocations are7314,7352,8380MiB on GPU0
and7393,7233,7233MiB on GPU1. No room for another simulator. Asked whether the
oldest RAM baseline78152/8771 at726 may be closed after archival; no response or
shutdown yet. Keep current RAM81115/8773 at753 and GPU recovery66502 untouched.

The oldest baseline's full2.3GB recordings were copied locally to
`runs/ram_baseline_full_backup/recordings/`. A checksum-mode rsync dry run
(`rsync -aznci`) completed with exit0 and no differences. Remote data remains.
This is an evidence backup, NOT a resumable physics snapshot: terminating the
worker loses its live state. No worker was reset/stopped to make room.

## Descent753 diagnosis: downward overshoot and integral windup

Correction to earlier wording: target z166.933mm, measured z162.612mm.
This is a4.320mm DOWNWARD OVERSHOOT, not stopping above the goal. Wrist-camera
calibration reconstructs the hand trajectory using a fixed camera-to-hand
transform inferred from terminal proprioception; preceding endpoint residuals
are below1.1e-7 in pose-vector norm. No object state enters this reconstruction.
At730 measured z167.353mm;735 z164.579mm;750 z162.472mm. Commanded joint FK also
passes below the goal, so this is not simply an actuator unable to reach it.

Replaying the OLD position integral against this trajectory yields -6.364mm
at730 and still -3.793mm at753. The accumulated downward ramp-lag compensation
continues pushing after the target crossing. This supports integral windup as
a contributor; it does not exclude contact or prove a counterfactual outcome.
Reproduce with `scripts/analyze_ram_descent.py --run
runs/ram_contact_preclosure_execution --wrist-depth
runs/ram_contact_recordings/bbd50fc209d44f9a84b12ee63827f0ff/wrist_depth`.

NativeDiffIKFeedback now clears a per-axis integral that opposes correction
after more than1mm target crossing. Same-direction load compensation and
submillimeter deadband are retained.262tests pass. This change is LOCAL ONLY:
held workers retain the old implementation; no hot patch/restart/motion.
Next physically qualify anti-windup in a separately labeled noncontact condition
before new near-holder descent. Do not close at753 or replay the failed target.
No RAM grasp, insertion, or task phase completed.

## Contact-view condition: rear-module approach and current support evidence

Separate worker81115 (remote8773/local18773), episode
`bbd50fc209d44f9a84b12ee63827f0ff`, uses the legal-start contact-view camera.
Fresh Astra selected the rear module, unlike earlier trials; this is not a
matched camera A/B. Its top pixel[425,146] deprojects to
[.419607,-.363420,.068533]m, with2.830mm local depth spread.
Open-hand approach completed249actions,2.516mm endpoint error, no guard stop.
Continuous intermediate transit used37actions per segment rather than64;
the final segment retained settling. No closure or RAM success at249.

Current249 images show the same historical pixels unoccluded. The extended
preclosure helper binds history to the earlier same-episode camera/pixels and
samples CURRENT depth; correspondence remains an explicit static-feature
assumption, not tracking. Seven rejection tests cover detached histories.

An initial review improperly inherited a hardcoded holder-height estimate from
earlier trials. That review was NOT executed. Removing the unsupported number
changed approval to inspect. Three newly operator-marked CURRENT support pixels
[370,151],[420,174],[470,197] measure48.32--48.37mm height. With these supplied
explicitly, review approves exploratory open-hand placement only: nominal
finger-end separation5.7mm from sampled surfaces, NOT minimum clearance or a
bound on hidden holder geometry. The prompt no longer hardcodes holder height.
These distinctions matter: review conclusions are sensitive to asserted evidence.

Reviewed preclosure rotation/descent executed504actions to observation753.
Rotation arrived; first descent waypoint passed. Final descent exhausted64actions
with4.323mm position error and0.001375rad rotation error, outside the unchanged
3mm arrival threshold. No tracking guard triggered, but runner stopped on
nonarrival: NO closure, lift, retry, or threshold relaxation. Cause is not yet
established; do not label this obstruction or merely insufficient settling.
Preserve worker81115 at753. Current right/wrist images show the module and pads
more clearly, but improved visibility is not task success. Next assess actual
endpoint/trace and a distinct supported action, not blind repetition of this goal.
See [current right view](evidence/ram_contact_preclosure_753/08_right.png),
[wrist](evidence/ram_contact_preclosure_753/08_wrist.png), and
[nonarrival receipt](evidence/ram_contact_preclosure_753/08_receipt.json).
Evidence: [view](evidence/ram_contact_approach_249/05_right.png),
[approach receipt](evidence/ram_contact_approach_249/05_receipt.json),
[measured plan](evidence/ram_contact_approach_249/plan.json).
Local run: `runs/ram_contact_preclosure_execution`; reviews retained under
`runs/ram_contact_preclosure_*review`.259tests pass, not phase completion.

## Live aimed720: placement passed, closure deferred, camera command rejected

Current episode `febb2e8b8f8c4b6ab1a7dd160701fbde:720`, worker79506/8772.
Operator-marked current220 top/axis pixels[320,70],[240,35],[360,85] passed legal
depth sampling. Center[.300880,-.361681,.068058]m. Astra approved preclosure only.
Robot-only waypoint IK preflight passed;500actions completed rotation and descent,
final2.128mm/0.000967rad error, no tracking guard stop. No closure/lift.

The aimed wrist shows both pads around the module, improving visibility versus
baseline726. Closure review nevertheless returns inspect: holder-to-finger
closing path remains unresolved. Do not call projected straddling a grasp.
See [wrist](evidence/ram_aimed_preclosure_720/08_wrist.png),
[receipt](evidence/ram_aimed_preclosure_720/08_receipt.json),
[closure review](evidence/ram_aimed_preclosure_720/closure_review.json).

One planned four-segment external-camera route was attempted, but its FIRST
request was rejected as `InputRejected` BEFORE execution. Fresh observe confirms
still720. Static right-camera y=.95 is outside the unchanged inspection envelope
y<=.7; metadata enabling camera controls did not establish a usable start pose.
The proposed final z=.20 was also below the envelope's .30m floor. Neither
boundary was widened; no request retried, no camera/arm movement or closure from
the rejected route. This was an agent planning/configuration error, not a physical
obstruction or model-control failure.

Fix prepared: launcher checks configured initial right-camera pose before GPU
startup when inspection is enabled. New `pc_ram_contact_view.json` places the
camera at[.08,-.58,.30], aimed at earlier legal measured grasp-region coordinates.
It is a SEPARATE condition, not loaded into79506. Robot wrist aim, physics and
limits remain unchanged.252tests pass including old-start rejection/new-start
acceptance. Rendering/contact visibility still needs native qualification.
Preserve both live RAM episodes; do not reset them or claim that changing a
source config changes an existing worker. Full RAM task/recovery remain undone.

## Camera-enabled live220: model-selected noncontact approach

Current episode `febb2e8b8f8c4b6ab1a7dd160701fbde:220`, worker79506,
remote8772/local18772. Fresh Astra Flex medium selected wrist[282,42] on the
upper loose module in its initial view. Legal depth sample[.296041,-.363292,
.056656]m passed the existing3x3 spread gate (9.610mm). This is a visible housing
anchor, NOT verified top/grasp geometry despite the model's top-strip wording.
It is sufficient here only for the explicit22cm world-up noncontact hand target;
do not derive bite depth from this sample in the next phase.

The open-hand attitude-preserving approach executed39+39+39+39+64=220 actions,
14.667 sim seconds, endpoint2.699mm/0.000255rad, no guard stop or retry.
No operator pixel substitution in this run. The phase/controller recipe remains
operator-defined; this is not an end-to-end autonomous grasp or assembly result.
The aimed wrist now shows both fingers at this standoff. Their visibility at the
lower bite pose and actual pad/support clearance remain untested.

Evidence: [wrist](evidence/ram_aimed_approach_220/04_wrist.png),
[left](evidence/ram_aimed_approach_220/04_left.png),
[model selection](evidence/ram_aimed_approach_220/target_review.json),
[receipt](evidence/ram_aimed_approach_220/04_receipt.json).
Current capture `runs/ram_aimed_capture220`, selected calibrated depth under
`runs/ram_aimed_recordings`. Next current-view top/axis measurement and reviewed
preclosure placement, then inspection using enabled camera controls if needed.
Original baseline-camera episode remains726; do not reset either worker.
No closure, lift or RAM task phase complete. No source/evaluator control inputs.

## New camera-enabled condition, original726 preserved

New separate live episode `febb2e8b8f8c4b6ab1a7dd160701fbde:0`, worker79506,
remote8772/local18772. This is NOT a continuation or reset of726. Original RAM
worker78152/8771 remains held at726, verified by a fresh public read after launch.
Other GPU episodes were not stopped. FLUX remains intentionally unloaded.

The prior RAM launch omitted existing inspection-camera support and pinch-centered
wrist aiming. This was a setup omission, not a model or physics limitation.
`configs/tasks/pc_ram_wrist_aim.json` changes only the robot-local wrist target
and explanatory notes versus baseline; instruction, external cameras, physics,
rate and limits remain unchanged. Launch explicitly includes
`--allow-inspection-camera --record-depth --allow-local-stages
--local-stage-rotation-integral`. Live metadata confirmed camera and gaze control
enabled plus `wrist_target_hand=[0,0,.1034]`. This is idealized simulated sensing,
not qualified physical camera hardware or baseline FLUX conditioning.

GPU1 had7433/24564MiB used before this separate launch, sufficient for another
simulator. No active scene was evicted. Initialization and one explicit new-worker
reset completed; zero commanded control actions or paid calls in this launch.
The new wrist image shows both loose modules and part of the gripper; inspection
at the future bite location is still untested. Do not claim the closure blocker
solved before seeing that view at actual preclosure.

Next: fresh targeting/heading for this camera condition, bounded preclosure, and
use a sensor-grounded external inspection if pads/support are still occluded.
Do not replay earlier pixel coordinates, which are invalid under the changed
wrist orientation. Retained run/capture: `runs/ram_aimed_20260930` on host and
`runs/ram_aimed_initial_capture` locally. Selected legal depth/calibration under
`runs/ram_aimed_recordings`. [Initial wrist view](evidence/ram_aimed_initial/000000_wrist.png).
251tests pass, including condition-isolation check; no new physical success.

## Closure review at726: visibility blocked, no closure

Fresh public read confirms726. Current-only Astra review returns inspect: both
inner pads and their relationship to the support are not resolved. A second
review adds genuinely new evidence: historical216 center/axis measurements,
current calibrated depth comparisons, robot-nominal pinch location and the
historical wrist image. This resolves some nominal-centering uncertainty but
still returns inspect. No contact, closure, lift or reset occurred.

Current nominal pinch is[.299744,-.360339,.060687]m, about0.29mm lateral from
the historical marked center and7.46mm below its top (planned bite5mm). One
historical axis point agrees with current wrist depth within0.001mm; center is
outside the wrist image but agrees within1.45mm in the left image. Other samples
are occluded/inconsistent. These are sparse consistency checks, not whole-object
stasis, structural contact, or holder-clearance certification.

The follow-up preserved the distinction between inferred centering and actual
contact visibility. This is a qualitative memory-use example, NOT a controlled
memory benefit or physical completion. Do not repeat unchanged-image reviews.
Evidence: [current only](evidence/ram_closure_review_726/current_only.json),
[with history](evidence/ram_closure_review_726/with_history.json),
[legal projections](evidence/ram_closure_review_726/projections.json).

The requested next observation is an oblique external view of both inner pads,
housing and support at the bite. Current RAM worker metadata has
`inspection_camera_enabled=false`: existing camera-motion API is unavailable in
this process. Preserve726; do not send unsupported camera commands, reset it to
enable a flag, blindly reposition, or silently treat inspect as closure approval.
Any new camera-enabled episode is a separate trial, not continued recovery.

Prepared but NOT exercised: explicit aperture and per-action tracking-guard
options in the contact probe, plus matching close-candidate review validation.
Proposed nominal4mm aperture/64-action hold was reviewed but NOT executed.
Existing GPU default remains unchanged.250tests pass; no grasp achieved.

## Live update: reviewed open-hand placement reached726

Current same episode `83ce804cdf06479ab757f513ab84185c:726`; RAM worker78152,
remote8771/local18771. FLUX remains intentionally unloaded. Do not reset.

Operator-marked current216 top-strip pixels center[285,100], axis[230,100] and
[340,100] deproject to a roughly world-y long axis. Center world position is
[.300034,-.360339,.068150]m; spread0.075mm. These are sensor surface samples,
not object pose truth. Hand x follows the axis, hand z points down; choose the
equivalent jaw heading with smaller rotation from current pose. Nominal5mm bite
and103.4mm pinch offset give target hand z166.55mm. Nominal112.9mm finger extent
leaves5.65mm above the previously measured ledge, NOT whole-holder certification.

Astra Flex medium approved open-hand preclosure only, explicitly noting the10mm
tracking guard is looser than that nominal clearance. The runner checks a matching
review, open hand, target formula and all waypoint robot-only IK before mutation.
It rotates at current elevated position before descending; never closes or lifts.
Unknown external clearance stays exploratory. No source collision/evaluator input.

Execution:9 segments,510 actions,34 simulated seconds. All intermediate segments
passed; rotation endpoint and final endpoint arrived. Final error2.474mm and
0.000653rad. No guard stop, retry, closure or lift. Final images show the module
still upright; fingers appear beside it but actual opposing contact is not yet
verified. This completes only bounded preclosure positioning, not a grasp or
assembly phase. Next: independent current-state closure decision, not another
target replay. Any closure needs explicit aperture/hold/stop bounds and separate
lift/retention verification.

Evidence: [left](evidence/ram_preclosure_726/08_left.png),
[wrist](evidence/ram_preclosure_726/08_wrist.png),
[receipt](evidence/ram_preclosure_726/08_receipt.json),
[review](evidence/ram_preclosure_726/review.json),
[sensor plan](evidence/ram_preclosure_726/source_plan.json).
`prepare_ram_preclosure.py` records the operator-selected pixels and measured
heading. `run_grounded_correction.py --preclosure-only` enforces no closure.
249tests pass; not evidence of task success.

## Live update: operator-assisted standoff reached216

New live episode `83ce804cdf06479ab757f513ab84185c:216`, worker PID78152,
remote8771/local18771. Previous observation-only episode remains closed.
FLUX is intentionally unloaded to retain this RAM scene; exact private restore
state is recorded outside artifacts at the path in the local run's
`retained_worker.json`. Do not launch FLUX alongside RAM without a memory check.
Other GPU episodes remain untouched. Do not reset the RAM episode.

Fresh Astra selected wrist[320,86], a lower ledge at z48mm rather than the
module's visible top at z68mm. That semantic selection was NOT executed or
counted as autonomous success. Previous[320,94] was a sloping/vertical side,
not merely a depth discontinuity: fitted normal is nearly horizontal. The
10mm spread gate alone cannot classify top surfaces or object identity.

Explicit operator correction selected current wrist[320,89], a visible solid
top strip. Its3x3 depth spread is0.068mm; point[.300545,-.360013,.068217]m.
The noncontact hand target is22cm world-up from that surface. Load-bearing
suitability remains unknown. No source object coordinates or evaluator were used.

New `--approach-only` mode preserves current hand attitude, requires an open
hand and tracking guard, excludes closure/descent/lift, and caps at512 actions.
This trial declared5 segments/320 maximum actions, executed38+38+38+38+64=216.
Final endpoint error2.574mm/0.000270rad,14.4 simulated seconds and93.93 execution
wall seconds. No guard stop, retry or closure. Intermediate stages did not settle;
only the final endpoint did. The module is better resolved in the final wrist
view. No grasp, installation, recovery or task phase completed.

Evidence: [wrist](evidence/ram_approach_216/04_wrist.png),
[left](evidence/ram_approach_216/04_left.png),
[receipt](evidence/ram_approach_216/04_receipt.json),
[source and operator label](evidence/ram_approach_216/source_plan.json).
Next: measure heading and contact patches from216, then bounded reorientation
and preclosure approach if justified. Do not use the GPU fixed heading.247tests
pass, including approach-only preservation/no-closure behavior; not task success.

Status: native RAM observation-only launch/capture completed. Zero commanded
control actions and zero model calls. No grasp, insertion or phase completion.

## Initial scene result

Episode `fa459b5bcfb745a2a6b9209f0839d684:0` was captured after one explicit
initial reset in a new temporary worker. Isaac initialization/warmup is not
counted as commanded control. The worker was then closed; this RAM episode is
NOT live/resumable. A physical trial needs a fresh episode and fresh targets.

- Both upright modules are visible in the left overview and wrist view. The
  wrist view crops part of the farther module; the nearer one is fully in frame.
- The right overview does not resolve DIMM insertion geometry. This is a usable
  discovery/pick starting view, not insertion readiness or certified clearance.
- Metadata confirms recorded depth, continuous transit, local DiffIK with
  rotation integral, contact tracking guard and upstream grasp-weld assistance.
- Initial launch reached readiness but capture helper was missing remotely;
  it exited without a reset request. Added prerequisite checks and synced helper.
  A subsequent preflight hit TCP TIME_WAIT, not a live worker; selected an unused
  port after checking listeners. No motion was retried.
- Idle FLUX was restored and authenticated ready as PID77661. Existing simulator
  processes were not terminated. GPU recovery was re-read afterward: still2813.
- All243 existing tests pass; the new resource probe was validated by this actual
  launch/cleanup, not by those component tests.

Evidence: [left](evidence/ram_initial_scene/000000_left.png),
[right](evidence/ram_initial_scene/000000_right.png),
[wrist](evidence/ram_initial_scene/000000_wrist.png),
[metadata](evidence/ram_initial_scene/metadata.json).
Local retained run: `runs/ram_initial_scene_capture_v2_20260930/` includes depth,
calibration, logs and restoration receipt. Script: `scripts/probe_ram_initial_scene.py`.
Next is a fresh bounded RAM grasp-selection/approach trial, not another startup
probe. Keep the same information contract below and do not reuse these targets
as current-state measurements.

## Why now

### Offline target selection follow-up

The old request builder hardcoded graphics-card identity. Added explicit
`--target-object ram_module` for approach/grasp selection only; GPU-specific
later stages reject it rather than silently issuing a wrong-object prompt.
Two regression tests added;245tests pass.

One Astra Flex medium call on the retained initial images chose the nearer
module at wrist[320,94], with long-axis samples[290,94] and[348,94]. Its grasp
claim was limited to a standoff hypothesis. Exact3x3 measured depth spreads were
10.851,9.649,10.859mm: center and second axis point FAIL the unchanged10mm gate.
No target admitted, no live action or phase completion. Raw smooth depth
variation can also trigger this gate; failure alone is not proof of mixed pixels.

Single-pixel diagnostic deprojection (NOT admitted as a motion target) shows an
approximately world-y axis at z55.3mm. Do not reuse the GPU recipe's fixed jaw
heading for this module. Neither those samples nor a nearby depth-continuous
pixel proves an upper load-bearing contact surface. Next live trial must obtain
current contact/axis evidence and derive jaw heading; do not apply cached pixels
as autonomous decisions or weaken the gate to get an approach command.

See [model selection](evidence/ram_initial_scene/target_review.json) and
[raw depth rejection](evidence/ram_initial_scene/depth_measurements.json).

The GPU episode remains at2813 with no supported contact recovery. Preserve it.
RAM is the next primary task in the original experiment sequence, not a claimed
recovery of the GPU failure. Success requires BOTH modules installed and isolated
native evaluation afterward. A first grasp/lift is an intermediate result only.

## Compatibility and evaluator-only audit

Existing `configs/tasks/pc_ram.json` passes `load_task`: registered
`assembly.pc_ram.franka.joint`, three640x360 cameras,15Hz control. The pinned
upstream registration supports the same Panda joint interface. Existing native
DiffIK, continuous intermediate waypoints and per-action tracking guards can be
used without a new controller implementation; live behavior is not yet tested.

The native robot preset starts RAM upright in holders. This is a benchmark
initialization aid, not a learned flat-object pickup result. Grasp-weld assistance
and authored invisible slot collision fixtures remain upstream defaults. This
does not solve the visual/physical-geometry mismatch found on the GPU task.
Do not feed source-derived object coordinates, slot dimensions or evaluator
tolerances into target generation. This audit is experiment selection context,
not policy input. Do not replay upstream smoke trajectories.

Sources: pinned `robobench/suites/assembly/configs/envs.py` RAM Franka registration
and `scenes/pc_ram_assembly.py` scene description. Existing task instruction stays:
"Install both loose RAM modules into the computer's DIMM slots. Verify their
placement visually." No dynamic `describe()` or extra source-derived instructions.

## Resource boundary

Measured host GPU usage:23186/24564MiB and22264/24564MiB. Do not launch a fourth
simulator into this headroom. Preserve the three existing simulator processes.
For an observation/local-control pilot, temporarily unload ONLY verified idle
FLUX, after capturing its exact command/environment securely and checking for
active requests. Restore it in cleanup and verify authenticated readiness.
Do not print tokens or retain environment secrets in experiment artifacts.
If it is busy, wait; do not kill unrelated work. A RAM-only local-control pilot
is NOT a FLUX hybrid trial. FLUX co-residency remains a separate resource issue.

## Bounded first trial

1. New isolated RAM worker and recording directory, unused loopback port;
   record legal RGB-D, enable local stages and existing rotation-integral feedback.
   Initial reset belongs only to this new episode. Keep cameras as configured;
   no geometry or grader changes. No camera sweep before examining the first view.
2. Capture initial observation, public calibration and metadata. Check image
   orientation, useful framing, measured aperture and matching observation IDs.
   If initial images cannot identify a module, stop and record the limitation.
3. One Astra Flex medium request identifies a visible module and suitable grasp
   feature using current RGB only. Depth-derived targets must come from that
   capture. Limit initial selection plus boundary review to two calls, total
   reservation cap$1, existing shared$75 ceiling and unresolved holds unchanged.
4. Qualify robot-only IK, workspace and approach from measured geometry. Do not
   reuse GPU pixel templates or call the fixed GPU recipe a RAM skill. Select
   bounded local EEF targets, continuous transit, unchanged per-action guards.
5. First physical scope ends at preclosure: open hand, at most512 control actions
   across the approach, no closure or insertion. Review fresh contact geometry
   once. Failure/ambiguous motion stops without reset, target extension or retry.
6. Only if the fresh contact evidence supports it, separately declare closure
   and short lift bounds. Verify visible retention/support clearance afterward.
   Then plan socket alignment from legal observations. A latched grasp score is
   not current retention, insertion or full task success.

## Evidence to retain

Task/config and source revision, cameras/physics assists, request/response and
cost, selected pixels and attached depth, exact action requests/receipts, first
failure and stop reason, chronological video with sim/wall timing, current
observation, and posthoc evaluator in a separate channel. Preserve negative
results. No full-phase claim until integrated native task success is verified.
