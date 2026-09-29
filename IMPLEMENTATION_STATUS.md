# Implementation status / next-agent handoff

## Current experiment status (September 30 JST)

CURRENT1675: robot-centerline-screened opposite view exposed socket endpoints.
Two current socket depth samples valid. Historical1547 connector propagation
predicts5.9/8.0mm paired horizontal offsets and~138mm vertical gap, conditional
on no slip. Housing/contact spans differ; no insertion permission. Next review
a bounded nearer standoff; see `docs/GUARDED_CARRY_CURRENT.md`.

CURRENT1611: connector endpoints measured at1547 (83.160mm separation, notch
reported visible), socket endpoints unresolved. Subsequent board-facing camera
view is forearm-occluded; no model call or descent on that view. Next viewpoint
must account for robot self-occlusion; see `docs/GUARDED_CARRY_CURRENT.md`.

LATEST1547: depth feedback corrected the bad connector association at1483;
rough axes1.095deg apart, sampled gap140.373mm. Endpoint correspondence still
unresolved. Closer PCB-side camera capture1547 is local for the next check;
no alignment correction/descent/insertion. See `docs/GUARDED_CARRY_CURRENT.md`.

NEWEST: held1483, elevated PCB-side view exposes contact strip. Fresh inventory
has one depth-inconsistent connector association (smooth background patch), so
its raw axis is unusable. Two socket rim samples remain consistent. No new
descent/insertion; see `docs/GUARDED_CARRY_CURRENT.md` for exact evidence.

LATEST: episode held at1419. One model-selected camera path passed preflight
and execution, but view is edge-on and case-rim occluded; no connector sample,
descent, insertion or release. See `docs/GUARDED_CARRY_CURRENT.md`.

NEWEST: same held episode now1355 after reviewed8cm closer-standoff attempt.
64-action budget ended4.306mm short; no guard stop, retry, insertion or release.
Candidate/executor duration mismatch is fixed for future reviewed standoffs;
old candidates rejected, no automatic replay.224 CPU tests pass. See
[latest continuation](docs/GUARDED_CARRY_CURRENT.md).

LATEST: guarded explicit 23 cm lift (707 actions) and elevated carry (328
actions) completed; same episode held at1227, no descent/release. History-aware
review recovered the socket with two valid depth samples, but connector remains
occluded. See [current evidence and corrected diagnosis](docs/GUARDED_CARRY_CURRENT.md).
Older payload-baseline claims below are historical and superseded: robot
configurations were not matched and the earlier stall cause is unresolved.

Project-wide handoff: [progress, results and remaining work](docs/PROJECT_PROGRESS_HANDOFF_20260930.md).

- Fresh guard-enabled integrated replay completed operator-defined approach,
  closure and5cm lift (590 actions; endpoint errors0.818mm/0.00302rad).
  Posthoc score remains0.3333/grasp rung. Two fresh carry reviews and three
  bounded camera moves still could not establish a card/support gap; no
  carry/descent issued. Meaningful negative evidence, not task success. See
  `docs/GUARDED_INTEGRATED_REPLAY_20260930.md`.

- Corrected lift interpretation: a separate+18cm retention probe visibly
  cleared the card but ended at the64-action budget; a separate+84mm
  continuation was natively stopped by the contact guard after6 actions.
  Full-target error84.947mm; cause unknown, no retry. Evaluator stayed0.3333.
  See `docs/GUARDED_VERTICAL_RETENTION_20260930.md`.

- Matched open-gripper baseline (fresh seed0, same controller/ramp/guard) ran
  9cm for64actions without a guard stop, ending3.793mm short. Held-card
  continuation stopped after6 actions at84.947mm full-target error. This
  points toward payload/grasp/collision interaction, not generic DiffIK failure;
  no guard relaxation or retry. See `docs/GUARDED_FREE_BASELINE_20260930.md`.

- Recovered1800 review with unchanged minimal instruction produced four valid
  sensor anchors: sampled connector/rim axes differ7.947deg, mostly yaw. Full
  pose and swept clearance remain unknown. No motion. First API output was
  truncated/rejected; compact fresh call valid, total$0.10638625.220tests.
  See `docs/RECOVERED_CONTINUATION_20260930.md`; stop further same-view reviews.

- Isolated native guard-enabled hold and1cm upward move passed (30+60actions,
  final0.247mm). Temporary worker closed; held-card episode unchanged. This is
  normal-path qualification only; native contact-stop branch remains untested.
  No new phase complete. See `docs/CONTACT_GUARD_QUALIFICATION_20260930.md`.

- Contact source audit found visual/collision geometry separation AND an
  instruction mismatch: upstream describes bracket-through-cutout assembly;
  our configured task only says align/seat. Exact failed contact is unproven.
  Keep this evaluator-side; do not derive motion from hidden fixture geometry.
  Next is an explicitly labeled instruction-contract comparison plus live guard
  qualification, not another blind descent. No phase completed. See
  `docs/CONTACT_OBSERVABILITY_AUDIT_20260930.md`.

- NEWEST held observation1800: explicit surface-contact hypothesis failed,
  26.291mm/0.176rad final error; posthoc native success=false,score0.3333. No
  extra push/release. Astra selected5cm withdrawal; it completed at1.600mm error,
  card visibly retained but tilted. New per-action contact tracking guard is
  CPU-tested, NOT loaded in current worker; contact runner now requires it.
  217tests; one recovery call$0.01484625. See `docs/CONTACT_HYPOTHESIS_20260930.md`.

- Latest held observation1651: projected sensor memory stabilizes socket identity;
  measured same-side endpoints supported an exploratory6cm near approach,84actions,
  final1.213mm. Close socket inspection still cannot resolve exact keyed endpoints.
  Five legal depth profiles across apparent channel are nearly planar, not a
  measured opening. No insertion/release. Next bounded contact hypothesis, not
  more exact-endpoint prompts on this same image.214tests; three calls$0.141445.
  See `docs/PROJECTED_CORRESPONDENCE_20260930.md` for limitations/live state.

- Newest: face-on view yielded two depth-supported connector samples without
  threshold changes. Exploratory 10 cm vertical standoff approach completed
  in 98 actions, 1.949 mm final error. Current held observation 1503; no insertion
  or release. Correspondence now sees connector ends but confuses socket identity.
  Original sensor anchor projects to [320,316], matching current depth within
  0.602 mm. Next projected-history correspondence review, not more camera sweeps.
  Two new calls $0.08973625; 209 tests. See `docs/MATING_FEATURES_20260930.md`.

- Latest continuation at held observation 1341: separate feature localization
  exposed a likely neighboring-slot switch when the original target was cropped.
  Labeled same-episode carry history plus reframing recovered consistent socket
  identity and two valid housing-depth samples. Connector recognized but current
  samples fail depth continuity; no insertion geometry or descent. Three new
  calls $0.1074575, 201 tests. See `docs/MATING_FEATURES_20260930.md`.

- Latest live trial: bounded camera aiming qualified, assisted lift replay
  completed in 693 actions, fresh sensor-feature carry completed in 328 actions
  with 1.957 mm final error. Final observation
  d3645c724ce046aeab7dbd48580af359:1213, held, paused; no descent/release. Two
  post-carry alignment reviews remain negative due to occluded mating features.
  Three calls $0.0632325. Same-episode carry runner added; 197 tests pass. See
  `docs/AIMED_LIFT_20260930.md`. This supersedes older current-worker notes below.

- Bounded camera aiming added; live observation 885 revalidated without motion.
  Fixed gaze limits motherboard framing. New gaze path/readback tests pass;
  current process does not contain the change. Next explicitly fresh integrated
  replay and sensor-derived aiming, not another fixed-gaze sweep. See
  `docs/CAMERA_AIM_20260930.md`. No task phase completed by this software change.

- Continuous transit live-qualified in a fixed-fixture assisted lift: 693 versus
  896 actions, 46.200 versus 59.733 sim seconds, 310.724 versus 400.042 execution
  seconds. Final 2.351 mm, clear_lift review, one call $0.0194525. Subsequent
  camera raises cleared the initial gray occlusion, but the socket is still
  unresolved at the overview scale. No carry or insertion. Last recorded
  episode 13b72700c14b45ecaca1f7e32103ae78:885. See `docs/SMOOTH_LIFT_20260930.md`.

- Added opt-in continuous transit to remove artificial holds at intermediate
  same-phase waypoints while retaining closure/final settling. Controller state
  persists across joins, actual action counts are recorded, guards remain.
  184 tests pass; native timing/retention validation completed as above.
  See `docs/CONTINUOUS_TRANSIT_20260930.md`.

- Independent inspection camera is now ported into opt-in local stages, with
  arm-hold/unchanged-gripper checks and camera readback failure stops. Software
  and live held-state translation tests passed; useful close socket viewing
  remains unresolved. No assembly phase completed by camera movement.
  See `docs/INTEGRATED_INSPECTION_CAMERA_20260930.md`.

- Current held-state inspection planning declined a <=5 cm non-descending hand
  move: no informative direction justified by existing views. No motion issued.
  The integrated worker lacks the older pilot's independent camera command;
  port that bounded capability next, rather than repeated grasp/view guesses.

- Close-target refresh trial now achieved visually reviewed assisted suspension:
  896 actions including approach, all strict arrival checks passed, final lift
  0.817 mm / 0.002588 rad. Fresh RGB-D target plus independent clear_lift review
  cost $0.0503675 (two calls). Operator recipe, assistance on, unknown clearance;
  not autonomous recovery or assembly. Paused at observation 896. Subsequent
  carry review returned inspect, slot occluded; no carry issued. Three-call
  total $0.072945. Lift video saved. See `docs/CLOSE_TARGET_20260930.md`.

- Fresh contact-integral trial: 640-action approach passed; closure passed even
  strict arrival (1.759 mm / 0.01035 rad). One 5 cm lift executed 64 actions,
  ending at 4.714 mm / 0.03341 rad error: exploratory completion passed,
  precision arrival did not. Images suggest upward card movement, but support
  clearance/retention remain unverified. Subsequent nine-image Astra review:
  partial_contact, $0.02803375. No further motion. Earlier successful pilot used
  a refreshed wrist target ~31 mm laterally away and a 23 cm rather than 5 cm
  lift; these are unresolved confounds, not evidence of controller failure.
  Next refresh close-range target and predeclare suspension test. 176 CPU tests
  passed. Operator recipe, cached target, grasp assistance on; no autonomous
  recovery or assembly claim. See `docs/CONTACT_INTEGRAL_20260930.md`.

- Wrist framing fixed in an opt-in condition: nominal closing line now 17/17
  samples in frame versus 0/17 originally. Matched 640-action open approach
  passed; visual review still inspect. Separate explicitly exploratory closure
  ran 64 actions but missed rotation arrival tolerance (0.04097 vs 0.03 rad),
  then stopped without lift/retry. No secure grasp or phase completion. Cached
  target provenance correction disclosed. See `docs/WRIST_AIM_20260930.md`.

- Oblique-view sensor approach ran without Hybrid replay: 640 open-gripper
  actions, ten endpoint passes, then pre-closure pause. Review supported rough
  centering but still requested inspection for occluded far pad/support gap.
  No closure or grasp attempt; two calls $0.06194875. Stop static-camera approach
  repetitions; next bounded held-pose view or calibrated pad/surface reasoning.
  See `docs/GRASP_OBLIQUE_20260930.md`. No phase newly completed.

- Outcome-blind review of retained pre-closure images returned inspect: opposing
  contacts/centering not established. Added opt-in pre-closure pause, tested to
  issue no closing commands (167 CPU tests). No new physical success. Next use
  a labeled oblique inspection view and stop for review before closure; do not
  repeat the full Hybrid approach just to test visibility. Review cost $0.02369.

- Corrected pose ramp now live-qualified in integrated correction: all 14 stages,
  896 actions, maximum endpoint error 1.596 mm. Card tilted/lifted at one end but
  remained partly supported; independent image review says partial_contact.
  No secure grasp, autonomous recovery or assembly success. Ten calls cost
  $0.97526375. Next improve observable grasp geometry, not repeat Hybrid wording
  sweeps or assume a continuous depth patch defines a grasp. See
  `docs/HYBRID_POSE_RAMP_20260930.md`.

- Latest same-episode Hybrid -> RGB-D correction attempted: 74 FLUX actions,
  then one fresh target call and a successful 5 cm local retract (1.582 mm error).
  Rotation failed before confirmed action due to a translation-only ramp inside
  the pose bridge. Halted without retry; no grasp. Fixed with bounded pose ramp,
  166 CPU tests pass; fresh GPU validation is next. Nine calls cost $0.92563625.
  See `docs/HYBRID_GROUNDED_20260930.md`. No experiment phase completed by this fix.

- Native GPU simulation, robot FK, live Astra Flex calls and FLUX prediction/FK
  qualification have run. First bounded FLUX Hybrid execution now ran: three
  accepted chunks, 24 joint actions, zero rejections, no grasp/task success.
  See `docs/HYBRID_FIRST_20260930.md`; manipulation competence remains unproven.
- Frozen privileged OSC reference replay succeeded through seating/release/retract
  in 1,859 actions, zero calls. This is not nonprivileged success.
- Sensor-target OSC captured/lifted with assistance but lost orientation (2.591 rad).
- Native DiffIK preserved orientation but initially fell 99 mm short of lift.
  Bounded translation integral plus a larger error cap then achieved a controlled
  assisted lift (1.945 mm, 0.02094 rad) and elevated carry (1.661 mm, 0.01778 rad).
- Nonprivileged insertion, completed task, adaptive recovery, matched mode comparisons
  and experience reuse remain OPEN. Mating-feature visibility is the current issue,
  not evidence that all motor control or perception problems are solved.
- The bounded sensor pilot ended at 3,130 actions, held=true but task=false.
  Two alignment reviews requested inspection; no insertion was attempted.
  Its 74 MB trace is backed up locally, with compact public evidence and video.
- The earlier next step was pre-grasp socket localization and retained geometry;
  coarse localization has since run, but precise entry geometry remains open.
- An explicitly changed overhead-right-camera condition exposed a candidate
  socket before carry. Lift/carry repeated, but hand/card occlusion remained
  afterward; a historical-context review recognized the prior socket without
  claiming present alignment. No insertion yet. See `docs/OVERHEAD_SOCKET_20260930.md`.
- Independent camera translation is now opt-in and live-tested while the arm
  holds. A Fabric-backed pose failure was detected; the pinned USD pose route
  passed. The idealized camera has no collision body. Post-carry use is recorded
  below; see `docs/INSPECTION_CAMERA_20260930.md` for the initial qualification.
- Post-carry independent views now supported a fresh contact-edge measurement,
  two reviewed closer approaches and one contact-intended attempt. All endpoints
  passed, but the native seating predicate remained false and the card stayed
  held. Four fresh calls cost $0.08531625. Precise correspondence remains unresolved;
  see `docs/POST_CARRY_CONTACT_20260930.md`. No release or successful recovery yet.
- Retained final-view correspondence review returned inspect, with no reliable
  paired endpoints. Earlier socket end_a had failed depth continuity; pre-grasp
  axis qualification was incomplete. Acquire higher-detail socket geometry before
  occlusion in the next trial. No additional motion was run in this review.
- 160 CPU tests pass. They do not establish manipulation robustness.
- Higher-detail pre-grasp capture completed with zero control actions. Three
  housing-rail samples passed depth continuity (about 0.626 mm spread); sampling
  improved to about 0.80 mm/px. Internal key/gap still unresolved. Camera position
  AND focal length changed; old right-camera pixel templates are invalid. See
  `docs/SOCKET_DETAIL_20260930.md`. This is sensing progress, not insertion success.
- Paired-rail review of the detailed socket view still returned inspect. Stop
  this camera/prompt branch; do not compensate by pressing farther down.
- Next: bounded longer Hybrid interval with target-relative progress assessment.
  Precision insertion correspondence remains unresolved and is not bypassed.
- Longer-prefix attempt stopped after 24 actions on its second review: no task
  success. Found and corrected a prompt ambiguity between EEF-command limits and
  joint-proposal FK displacement, without changing validation. Clarified-prompt
  live results follow below; see `docs/HYBRID_LONGER_20260930.md` for that stop.
- Clarified-prompt trial and explicit same-episode continuation now executed 88
  FLUX actions through approach/closure/short lift-test. Card remained visibly
  supported; reviewer stopped, no verified grasp or success. Eight calls cost
  $1.08917125. Next inspect missed grasp and bounded recovery eligibility, not
  further blind transport. See `docs/HYBRID_GRASP_ATTEMPT_20260930.md`.
- Robot-only projection audit places nominal pinch center outside the wrist
  image (v=-41 px). Added explicit pad-center geometry to reviewer context.
  Follow-up stopped after 32 actions under the fixed two-uncertain-chunk rule;
  that rule was removed as an unjustified early cutoff, not a validator change.
  Revised-rule live test remains next. See `docs/PINCH_VISIBILITY_20260930.md`.
- Revised-rule live test completed: 76 FLUX actions, seven calls, $0.76792875.
  Reviewer detected premature closure/transport with fingers above/beside card
  and stopped. No correction or grasp. Stop prompt-only approach repetitions;
  next test a legal RGB-D-grounded correction stage. See
  `docs/HYBRID_MISALIGNMENT_20260930.md`.
- Opt-in same-worker local correction bridge implemented and small unloaded
  offset live-qualified: 1 cm upward ended within 0.246 mm, zero paid calls.
  First attempt exposed a receipt-count mismatch after motion; halted without
  retry, then fixed preflight to cap 64. No contact/correction success yet.
  Next integrate fresh RGB-D correction after Hybrid misalignment in the same
  episode. See `docs/LOCAL_STAGE_BRIDGE_20260930.md`.

See [native DiffIK evidence](docs/SENSOR_DIFFIK_PILOT_20260929.md),
[stage sequence](docs/STAGE_EXECUTION_20260929.md), and
[privileged reference audit](docs/REFERENCE_TRANSFER_20260929.md).
All sensor pilots retain grasp assistance and unknown swept clearance. They use
operator-defined phase recipes and are not autonomous full-task success claims.

## Original pre-GPU build snapshot

The sections below record the original delivery, not current GPU progress.
**Build:** 2026-09-29, version 0.1.0.

## Completed and tested on CPU

- Typed single-arm observation/action/receipt contracts; open-vs-closed gripper conversion.
- World-frame SE(3) action integration; wxyz quaternion handling; Euclidean motion bounds.
- Robot-only URDF FK, Jacobian, damped IK, joint limits and continuity validation.
- Exact upstream RoboICL anchored-memory helper, with immutable execution records and gaps.
- Single-arm direct-delta, direct-absolute, and hybrid reviewer/controller ports.
- Explicitly configured Responses client with strict action schema, usage accounting,
  time/call budgets, and no implicit endpoint/model fallback or execution retry.
- Authenticated loopback worker transport; one episode per simulator worker; duplicate
  command handling; stale-observation rejection; ambiguous-execution stop behavior.
- Complete fixture rollouts through all three modes, both in-process and over loopback HTTP.
- Policy-context allowlisting with tests that host-only evaluator sentinels never enter requests.
- Event/frame integrity checks, self-contained HTML reports, descriptive CSV/JSON comparison.
- Task configurations, pinned source-fetch plan, native RoboICL profile generator, documentation.

The exact test output and counts for this delivered build are in **VALIDATION.md**.

## Implemented but not exercised against the real dependency

**EmbodiedSWE GPU worker.** Uses the pinned `EvalSim` API, adds two explicit exterior
cameras plus the real wrist view, reads robot proprioception, qualifies FK, executes joint
commands, runs the native grader outside the policy context, and writes per-latch frames.
No Isaac Sim environment, assets, graphics driver, or real contact dynamics were available here.

**FLUX worker.** Calls the inspected standalone DROID policy API. Camera/state conversion
is unit-tested, but no checkpoint/encoder has been loaded and no FLUX output produced here.
Camera distributions, source rate, target dynamics, and task competence remain unknown.

**Live GPT client.** Request/response/error behavior is tested with HTTP mocks only.
No paid endpoint/model, xhigh/medium comparison, account access, or latency measurement occurred.

**Campaign supervisor and continuous video command.** Written and syntax/CLI checked.
A native GPU campaign and native rollout video have not been executed.

## Not implemented / intentionally deferred

- Exact end-to-end reproduction of the dual-arm RoboICL benchmark or full Codex Direct runtime.
  We preserve source pins and provide a native-profile helper, but our single-arm ports differ.
- Automatic memory-summary generation/retrieval optimization. A typed unverified-summary hook
  exists; no compression model, learned summarizer, or benefit claim exists.
- Automatic Hybrid→Direct mode switching or multi-proposal execution without GPT review.
- Task-specific post-training, policy distillation, force/tactile controllers, collision-aware
  motion planning, automatic calibration, real2sim reconstruction, real hardware operation.
- A demonstrated GPU, RAM, bulb, or other manipulation success. **None has been observed here.**
- Quantified robustness, recovery improvement, latency improvement, ROI, or sim-to-real transfer.

## Source findings that affect the plan

1. The GPU scene enables grasp welding by default. Preserve/record it and disclose it; do not
   describe a successful assisted grasp as unassisted physical generalization.
2. FLUX DROID emits joint targets, not EEF deltas. It requires three distinct views and a
   matching Panda joint order. Its PC-assembly competence is unverified.
3. The published RoboICL profile uses a third-party API endpoint/alias. The package never
   forwards credentials there implicitly.
4. The original full Codex direct agent is different from the constrained single-Act Direct-B
   port. Treat this as a changed experimental condition.
5. The environment pauses while reasoning occurs. Video simulated-time speed is not wall time.

## First hour on the GPU machine

1. Fetch/check the pins and install the upstream simulator environment.
2. Run one **capture-only** GPU scene. Check camera coverage and the FK qualification.
3. Restart the worker. Run Direct-A for just 3 decisions to test API/schema/control plumbing.
4. Independently load FLUX in its separate environment. Probe its output on a captured scene
   without execution. Inspect joint/FK magnitudes and the camera contract.
5. Only then run a small Hybrid trial. Use `pc_gpu`; add `pc_ram` after the bridge is behaving.

Stop and fix an interface or dynamics issue before running long episodes. Do not run broad
benchmark sweeps, download every dataset, or port to another GPU software stack first.

## Most likely GPU-side fixes needed

- Camera coverage and physical camera calibration differ from the model's training rig.
- Isaac renderer/plugin setup or assets may require environment-specific installation.
- Panda URDF/root/hand-frame mismatch may trigger FK qualification; investigate, do not bypass.
- Joint-PD/IK may lack the contact behavior needed for insertion/threading. The source offers
  OSC/impedance modes, but this release does not implement equivalent joint-policy/EEF mixed
  control over those modes. Any change must be separately logged/qualified.
- FLUX dependencies and referenced encoder caches must match its pinned environment.
- Provider Responses compatibility and exact model ID need your account-specific verification.

## Validation interpretation

A CPU fixture pass means the software loop is internally consistent. It says nothing about
whether the visual model recognizes the component, whether the motor policy generalizes, or
whether contact dynamics permit the task. Keep `examples/cpu_fixture` out of investor robot
videos; those examples exist solely to make the implementation inspectable without a GPU.
