# Implementation status / next-agent handoff

## Current experiment status (September 30 JST)

Prepared open-stage dwell fix: conservative open-hand motion can end after4
stable pose/aperture samples at completed ramp; closure/camera timing unchanged.
307tests pass. NOT loaded into current88111/563, no new physical qualification.
Next task work remains better-observed grasp alignment, not additional speed sweeps.

Latest recovery: model-reviewed open-in-place at533 completed30guarded actions,
now563,2.427mm endpoint error, measured aperture99.59%. Card appears supported;
no grasp/lift. Distinct operator-scoped recovery, not Direct success. Current
worker88111/8774. Target patch remains occluded; next supported view/retreat and
depth-grounded target, no blind reclosure. See GPU_FAST_EXECUTION_PLAN.

Latest physical state: enhanced Direct-A episode8838a36a428c40c38aa6270f759398e4:533
held after stationary closure hit contact tracking guard (10.991mm error).
10calls total,$0.71696875,533actions; no verified grasp/native success. Earlier
lift test failed capture; model tried deeper alignment, final closure guard-stop.
No retry/lift/reset. Next legal depth/pad alignment diagnosis and distinct recovery;
not more speed sweeps. Full progression in GPU_FAST_EXECUTION_PLAN.

LIVE enhanced Direct-A first3calls: all3fast destinations arrived,120actions,
8sim/88.099wall seconds,$0.09263375. Endpoint errors0.298/0.338/0.385mm. Open
gripper now above GPU; no grasp/contact/installation, native score0. Includes
lateral/descent evidence; not arbitrary-rotation or payload qualification.
Worker88111/8774 held at8838a36a428c40c38aa6270f759398e4:120. Continue bounded
from fresh current observation plus prior memory, not reset. Details GPU_FAST_EXECUTION_PLAN.

Latest: enhanced GPU launcher and explicit20cm/0.30rad EEF task config prepared;
307tests pass. Direct horizon1,64actual-action budget per decision, fast eligible
transit standard in --enhanced-gpu mode. Native joint limits/timing unchanged.
No new physical/model trial. Fresh GPU inventory confirms six retained workers;
next archive temporary qualification evidence and launch fresh task episode.
Private launcher is outside public Git; public config/guard/tests are versioned.

Authoritative next sequence: `docs/GPU_FAST_EXECUTION_PLAN.md`, Current Decision
After External Review. Shared local execution AND opt-in fast-profile selection
are implemented;306tests pass. Use both flags as the standard next enhanced GPU
experiment configuration once the private launcher and larger explicit target
limits are ready. The generic CLI remains opt-in; no runtime default was changed
by this documentation update. No new physical trial since the5x vertical pass
and10x guard stop. Loaded carry, lateral/rotation, installation and recovery
remain unqualified or unsuccessful. Post-training is a proposed separately scoped
investigation, not running. See `docs/RESEARCH_HANDOFF_LOCAL_EXECUTION_20260930.md`.

## Historical Updates (Newest First; Superseded Where Noted Above)

Enhanced shared policy EEF execution now connected via --local-eef-execution:
one destination/local feedback, actual budget accounting and memory receipts,
stop-without-retry, native FLUX joints unchanged. Conservative profile only in
this integrated mode; fast selection/task limits still pending. CPU contract tests,
not live-model manipulation evidence. See GPU_FAST_EXECUTION_PLAN.

PHYSICAL SPEED RESULT:5x+feedforward passed12cm up/return68actions,4.533sim
seconds, endpoint0.336/0.216mm.3.07x faster elapsed sim time than conservative.
Subsequent10x attempt guard-stopped8actions; no return/retry. Retained worker86507
remote8774/local18774, episode4d39db60cb234fbf899be392416bddea:76.
Stop serial speed tuning; carry forward5x unloaded vertical evidence toward GPU
manipulation. Rotation/payload/contact unqualified. See GPU_FAST_EXECUTION_PLAN.

5x diagnosis: command increments max0.018153rad<0.06rad/tick, so observed stop
was not per-tick joint-command rate saturation. Optional one-step trajectory
feedforward added for fast smooth qualification only, unchanged tracking/caps.
Not physically tested or loaded into held85321. Next separate fresh fast trial;
no retry of stopped episode. See GPU_FAST_EXECUTION_PLAN.

5x smooth-transit native trial stopped at11actions:11.093mm moving-target lag
exceeded10mm guard.20.302mm upward progress; no return/retry/10x. Worker85321/8774
holds episode76c94f90d92e476f827641d75829d382:11. Prior unloaded conservative
qualification preserved as evidence; its worker84047 retired. Fast controller
integration now exists (276tests), but5x NOT qualified. Next bandwidth/feedforward
diagnosis. Other original five scenes preserved. See GPU_FAST_EXECUTION_PLAN.

NEW physical evidence: GPU-condition anti-windup unloaded12cm up/return PASSED.
Worker84047/8774(local18774), episode20e8a36447af44088fa373cf8782e9ca:209.
209actions,13.933sim/89.271execution wall seconds. Endpoint errors0.080/0.074mm,
no guard stop. No model calls, grasp or task success. Retained at209; old five
workers untouched. Next faster trajectory integration/qualification. See GPU_FAST_EXECUTION_PLAN.

User approved retiring RAM baseline78152 at726. Full recordings checksum-verified
again, then SIGTERM issued; cleanup retained5.1GB, so exact PID force-stopped.
Other five GPU processes remained present. Baseline live physics state is gone;
local/remote evidence retained. One simulator slot is now free for GPU-first
qualification. This supersedes pending-capacity notes below; no new motion yet.

Prepared explicit elevated/open-hand2x speed profile (45mm/s,0.12rad/s), with
default/contact rates unchanged. Qualification runner checks worker capability.
267tests pass; NOT deployed or physically qualified. GPU-first plan contains
the bounds and continuation sequence. Simulator-slot decision remains pending.

USER DIRECTION: GPU-first; suspend RAM experiments. Qualify reliable faster local
motion, then GPU manipulation and matched enhanced Direct-A/Direct-B/Hybrid.
See `docs/GPU_FAST_EXECUTION_PLAN.md`. Keep native FLUX joint execution distinct
from GPT/local EEF fallback. No matched comparison or speed qualification yet.

Noncontact anti-windup qualification runner prepared (max256actions), not run.
265tests. All six workers still occupy nearly both GPUs. Baseline726 full2.3GB
recordings backed up locally, checksum dry-run matches. Awaiting scene-retention
decision before closing only baseline78152; no worker reset/stopped. Current753
and GPU recovery2813 preserved. See RAM_FIRST_TRIAL.md for exact runner/options.

753 diagnosis: actual hand OVERSHOT downward4.320mm; it did not stop above
the goal. Wrist-calibration reconstruction and commanded FK support position
integral windup (-6.364mm near target crossing). Local anti-windup change clears
opposing per-axis integral beyond1mm crossing;262tests. NOT loaded in held
workers or physically qualified. Next separate noncontact qualification before
near-holder motion; no closure/retry at753. See RAM_FIRST_TRIAL.md.

LIVE contact-view RAM753: episodebbd50fc209d44f9a84b12ee63827f0ff, worker81115
remote8773/local18773. Rear-module model selection and249-action approach passed.
Reviewed504-action preclosure ended4.323mm from target: strict nonarrival, no
closure/lift/retry. Other scenes preserved. Current legal holder samples replaced
an unsupported inherited prompt estimate before motion. Historical-pixel binding
and explicit holder sampling added;259tests pass. No RAM task phase completed.
See `docs/RAM_FIRST_TRIAL.md` for evidence and next-action constraints.

LIVE aimed RAM720:500-action measured-axis preclosure passed,2.128mm error;
both pads now visible but closure review still inspect. External camera FIRST
request rejected before action: initial y=.95 outside inspection envelope; chosen
final z=.20 also invalid. Confirmed still720, no closure/reset. Startup check and
separate pc_ram_contact_view config prepared, NOT loaded.252tests. This is an
agent configuration/planning error, not physical impossibility. See RAM_FIRST_TRIAL.

LIVE camera-enabled RAM220: fresh model-selected housing anchor + legal depth
produced220-action open-hand standoff,2.699mm error, no guard stop. No operator
pixel correction in this approach, but recipe remains operator-defined. Both
fingers visible at standoff; bite-pose visibility untested. Same worker79506;
old RAM726 preserved. Next top/axis measurement and reviewed preclosure, not
grasping from this coarse surface anchor. See `docs/RAM_FIRST_TRIAL.md`.

NEW camera-enabled RAM: episodefebb2e8b8f8c4b6ab1a7dd160701fbde:0,
worker79506 remote8772/local18772, initial capture done. Wrist pinch aiming and
inspection/gaze controls confirmed enabled. Original RAM726 preserved on8771;
no reset of it, no eviction. FLUX remains unloaded.251tests. Next fresh targeting
and preclosure in the separately labeled camera condition; no grasp yet.

RAM726 closure BLOCKED by visibility: current-only and history+current-depth
reviews both say inspect. History supports nominal centering, not pad/holder
clearance. No closure/lift/reset. Current worker lacks movable-camera flag;
do not guess hand motion or reset preserved episode to enable it. See
`docs/RAM_FIRST_TRIAL.md`. Prepared guarded aperture-specific closure remains
unexecuted;250tests are software evidence only. FLUX still intentionally unloaded.

LIVE RAM726: measured-axis reorientation and reviewed open-hand preclosure
placement completed510 actions,2.474mm final error, no guard stop/closure/lift.
Module remains upright; opposing contact not yet verified. Same RAM worker78152;
FLUX intentionally unloaded.249tests. Next separate current-state closure review,
then bounded closure/lift only if supported. See `docs/RAM_FIRST_TRIAL.md`.

LIVE RAM216: operator-corrected legal-depth standoff completed216 actions,
2.574mm final error, no guard stop/closure. Fresh model pixel was rejected as
support ledge; this is not autonomous targeting. Worker78152 remote8771/local18771;
FLUX intentionally unloaded, private restart state retained. Other GPU episodes
untouched.247tests. Next current-view heading/contact qualification then grasp,
not reset/startup repetition. Details/evidence in `docs/RAM_FIRST_TRIAL.md`.

LATEST RAM offline selector: fixed GPU-hardcoded prompt with explicit RAM option.
Astra located a module, but exact center/one axis sample fail10mm depth spread;
no target or action admitted. Diagnostic heading differs from fixed GPU recipe.
245tests; see `docs/RAM_FIRST_TRIAL.md`. Fresh heading/contact evidence needed,
not silent pixel-template or fixed-GPU-attitude reuse. RAM episode remains closed.

LATEST RAM initial native capture completed, zero commanded actions/model calls.
Both modules visible; socket geometry unresolved in overview. Temporary worker
closed, FLUX restored/authenticated PID77661, GPU recovery rechecked2813 unchanged.
See `docs/RAM_FIRST_TRIAL.md` and public images. No RAM grasp or phase complete.
Next launch should run bounded grasp selection/approach, not repeat startup QA.

NEXT independent task: RAM configuration/source compatibility preflight passed;
no RAM simulator launch or physical result. See `docs/RAM_FIRST_TRIAL.md` for
bounded protocol and resource requirement. Both GPUs are nearly full; temporary
verified-idle FLUX unload is needed without disturbing held GPU episodes.
GPU recovery remains incomplete and is not replaced by this separate task.

LATEST strategy review: live observation remains2813. One Astra Flex medium
review returned stop: local-edge pinch is only a hypothesis without opposing
contact/gap evidence; no justified push/pivot either. No motion/reset. Record in
`docs/GRASPGENX_RECOVERY_PROPOSALS.md`; do not repeat unchanged-image reviews.
Recovery remains evidence-blocked, not proven physically impossible.

LATEST offline2813 geometry screen supersedes lowering the workspace floor:
nominal gripper bodies extend below the measured tabletop plane and several
poses overlap measured surfaces (not certified native collision checks).
Expanded planar cloud rejected pending semantic review. No new motion/call or
phase completion. See `docs/GRASPGENX_RECOVERY_PROPOSALS.md` for rejection evidence.

NEW2813 GraspGen-X:8 proposals/0.688s, zero actions or paid calls. All violate
120mm hand-height floor;3/8 endpoint IK converged. Canonical/Panda frame offset
handled. No candidate admitted. FLUX restored PID75277; all simulator episodes
preserved and2813 rechecked. Next qualify workspace/access, not more batches.
See `docs/GRASPGENX_RECOVERY_PROPOSALS.md`.243tests; no phase completed.

CURRENT2813: failed-approach trace shows persistent x error and increasing
rotation error, not continued convergence. One reviewed retreat completed20
single-latch updates with image review and stricter orientation/progress stops:
25.7mm actual withdrawal,1.46mm endpoint residual, no worsening observed.
No regrasp/reset/retry; cause of prior obstruction unresolved. Pending final
transit context must be accounted for at the next phase.240tests, calls4399.
See `docs/GUARDED_CARRY_CURRENT.md`; assembly/recovery remain incomplete.

CURRENT2793: reviewed inclined recovery approach physically tested without
lowering pilot bounds. Reorientation succeeded; final standoff FAILED arrival
at2729 (9.369mm/0.0596rad error).534actions, no guard trigger, retry or closure.
Camera-only hold restored interior view at2793. Cause unresolved; inspect fresh
proximity evidence before any different action. New executor and234tests;
recovery/assembly still incomplete. Calls4398. See `docs/GUARDED_CARRY_CURRENT.md`.

NEW2195 geometry: visible terminal span115mm exceeds80mm nominal jaws for a
full-width top-down straddle. A sideways-pinch hypothesis has convergent
robot-only IK but requires hand z64mm, below the120mm local-stage pilot floor.
Opposing contact/access also unobserved. No gate change or motion. Next assess
an inclined edge grasp within bounds or separately qualify a lower-hand
workspace; no blind reorientation toward an inadmissible endpoint. Calls4397.
See `docs/GUARDED_CARRY_CURRENT.md` for measured evidence and limitations.

CURRENT2195: completed the capped10mm wrist retreat in five2mm targets with
visual checks between stages.80actions; actual9.948mm up, no guard stop. Final
view still does not resolve an underside grasp surface. Stop this inspection
route; no closure, reset, paid call or recovery success. Selected RGB-D saved.
Next requires a concrete geometry-grounded grasp hypothesis, not another tiny
retreat. See `docs/GUARDED_CARRY_CURRENT.md` and public checkpoint receipts.

CURRENT2115: one depth-aimed free-edge camera inspection completed64 hold
actions but sees the exterior case wall. No regrasp/contact/reset. Stop nearby
low-view sweeps; use retained interior evidence for a bounded recovery proposal.
Recovery/assembly remain incomplete. See `docs/GUARDED_CARRY_CURRENT.md`.
Fresh2115 review proposed only a10mm wrist retreat with2mm visual checks;
not executed. No grasp selected, no evidence of physical impossibility. Do not
silently replace those checks with an unmonitored motion or repeat camera sweeps.
All CURRENT entries below are historical checkpoints.

CURRENT2051: failed placement remains displaced. Recovery review1987 selected
inspect/no grasp. Opposite view2051 shows PCB-up card across board, cooler
underneath, partially case-rim occluded. No blind regrasp or reset. Need a fresh
accessible mechanical edge/bracket candidate; see `docs/GUARDED_CARRY_CURRENT.md`.

CURRENT1987: release + open-hand withdrawal revealed FAILED seating. Card
tipped onto motherboard region. Posthoc native success=false, score0.33333334;
not supplied to control. Hand tracking passed, placement did not. Preserve
displaced state for new visual recovery; do not repeat straight-down recipe.
See `docs/GUARDED_CARRY_CURRENT.md` and its public image/receipt evidence.

CURRENT1893: reviewed guarded75.867mm contact-plane approach reached strict
arrival (90actions,2.493mm/0.018101rad), no guard stop, extra push or release.
Fresh1803 connector endpoint agreed with retained prediction within0.9mm.
Seating/assembly NOT verified; inspect current evidence before release. See
`docs/GUARDED_CARRY_CURRENT.md`.

CURRENT1739: reviewed guarded6cm nearer standoff passed strict arrival
(2.696mm/0.001402rad),64actions, no guard stop or retry. Image suggests retained
card closer to socket, not seating. No insertion/release. See
`docs/GUARDED_CARRY_CURRENT.md`; next inspect actual near-state before contact.

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
