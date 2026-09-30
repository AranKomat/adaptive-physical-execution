# GPU-first efficient execution and matched comparison

## Current Decision After External Review (September 30)

This section is authoritative; the chronological notes below retain earlier
states and must not be read as current instructions.

DEPTH CONTACT CONTINUATION: worker90072/8774, same episode
c6a13a2ac0f6489a858b059df0d79d99. Continuation from step195 used6 Astra Flex
medium calls and139 simulator actions. The gripper closed with tracking error
below1mm, then lifted25mm and arrived, but the card stayed on its support; the
gripper reopened. This is a failed grasp, not a local-DiffIK tracking failure.
At step334 the model made a second bounded regrasp attempt, consumed3 calls on
valid depth queries, and stopped without motion because it could not establish
pad/object straddling. Native score0, no guard/rejection, no privileged policy
input. Evidence: runs/gpu_depth_direct_a_continue7_20260930 and
runs/gpu_depth_direct_a_regrasp8_20260930. Shared calls4456.

DEPTH QUERY LOOP FIX: a valid first depth query now disables a second query at
the same observation; a second query remains available only when the first has
no usable measured sample. The next decision must act or stop, preventing a
query-only paid-call loop. Tests:315 passed. This is a control-loop guard, not
a claim that the grasp geometry is solved. Next physical trial should use a
fresh episode or an explicitly bounded continuation with a real reposition
proposal, then measure grasp/lift outcome.

DEPTH-GUARD CONFIRMATION: continuation from step334 with the new rule used5
Astra Flex medium calls. After one valid query, Astra lowered the open pads
27mm, closed successfully, and requested a20mm lift. The reposition and
closure both arrived with sub-mm tracking error. The loaded lift consumed its
64-action local-stage budget and stopped8.5mm short; the runner correctly did
not retry. Native score0 and no verified lift. This is meaningful progress on
grasp staging, but exposes a loaded/contact local-stage duration or force
tracking limitation. Evidence: runs/gpu_depth_direct_a_regrasp_guard9_20260930.
Do not resume the unfinished target; qualify a shorter loaded lift or a
separate contact-aware profile in a fresh bounded trial.

DEPTH-LED STAGING RECOVERY: current90072/8774 episode
c6a13a2ac0f6489a858b059df0d79d99:155. Explicit ramp-budget recovery checks prior
receipt reason, full budget consumption, open conservative profile, nominal ramp
longer than executed duration, same observation and prior trace; requires fresh
valid depth before a distinct target (old unfinished target rejected). Guard or
ambiguous stops remain ineligible. First6-call attempt only queried repeatedly,
zero motion: prompt still said obtain fresh depth even after success. Corrected
prompt marks prerequisite satisfied; max2queries per observation, explicit stop
option avoids forced action. Then3calls: query ->5cm shorter descent ->new query.
Model cited measured~.144m top vs~.2235m pinch and chose~.029m standoff remaining.
39actions,2.6sim/16.614execution wall seconds,0.689mm endpoint error, no guard;
whole segment38.542wall seconds,$0.2132525. Settling fix has native evidence for
this open-hand stage (not closure/payload). No grasp/contact success. Full trace
verified; evidence gpu_depth_replanned155.314tests pass. Shared calls4441.
Next bounded continuation from155 with its trace toward contact geometry; no
fresh reset needed. Queries at155 exist in trace but current continuation memory
does not import query results, so must re-query or add explicit same-ID binding.

FIRST LIVE DEPTH DIRECT TRIAL: worker90072/8774, fresh episode
c6a13a2ac0f6489a858b059df0d79d99 now116.5calls (3queries/2actions),$0.0721255,
116actions,7.733sim/80.065wall seconds. First query incorrectly used collage
coordinates (all3rejected); next queries supplied current measurements and model
selected motion. Fast~19.5cm approach arrived52actions,0.416mm error. Next18cm
descent selected conservative profile because endpoint below.30m;64actions could
not complete its ramp, stopped with83.17mm endpoint error (no tracking guard,
no retry/contact/grasp). This is a harness duration mismatch, not a demonstrated
depth-reasoning failure. Trace/image verified; evidence gpu_depth_direct_a_first6.

FIXES after this evidence: depth-enabled Direct now renders separate camera views
and supplies each camera's pixel dimensions, explicitly forbidding collage pixel
coordinates. Policy-stage preflight rejects conservative ramps whose nominal
duration+4settling actions exceeds current budget BEFORE execution; model prompt
states conservative64-action limits~9cm/.24rad and need for staging.313tests pass.
These are Mac-side fixes; no worker restart needed for future policy runs, but
current stopped116 must not automatically retry. Old88111/563 retired after
full1.8GB checksum-verified backup at runs/gpu_enhanced_direct_a_full_backup;
live physics no longer recoverable. Other older workers untouched. Current90072
loads open-stage settling and depth RPC; next supported distinct continuation
or fresh comparison must be explicitly labeled. Shared reserved calls4432.

DIRECT DEPTH LOOP IMPLEMENTED (not live-deployed): --depth-queries enables
measure_depth decisions with1..6pixels and no actions. Each consumes the usual
decision/API budget; /depth-points returns current recorded sensor measurements
and hand-frame offsets, rejects stale IDs, excludes scene/evaluator data. The
following Direct decision sees results only while observation ID matches; motion
invalidates them. Manifest marks depth input, trace records selections/results.
Private authorized launcher exposes the same flag with --enhanced-gpu, preserving
ledger/holds. Direct-A/B only for now; Hybrid is explicitly rejected until its
proposal/query scheduling is integrated. This changes observation access and must
be matched across future comparisons.312tests pass; fixture
query->action sequence proves accounting and stale-feedback removal, not robotics.
Current88111/563 lacks this endpoint; no hot reload/reset or physical progress
claimed. Next provision this revision on a fresh worker after preserving the
current scene's evidence, then run bounded depth-enabled approach/grasp.

DEPTH FEEDBACK PILOT AT563: two bounded Astra calls selected5visible pixels and
reviewed calibrated3D hand-frame offsets; all5depth neighborhoods passed. New
scripts/grasp_surface_feedback.py implements selection -> deterministic depth
measurement -> review, observation-only. It rejects stale selection/calibration,
limits6samples, and supplies no coordinates for rejected patches.309tests pass.
This is NOT yet an integrated Direct tool or a motion result. Crucially, review
correctly rejected the inference that positive closing-axis surface offset alone
proves miscentering. Samples on card lie handX~-25to-31mm versus pad samples+2to4mm,
and handZ111to130mm versus nominal pinch103.4mm. But off-center samples are not
corresponding contact sections; none of these offsets is a motion target. Need
corresponding surface/pad extent geometry. This demonstrates useful interpretation
of numeric depth feedback, not reliable grasp planning or proof of failure cause.
Earlier RGB-only trials did not supply depth to GPT and cannot test its depth
understanding. Evidence: docs/evidence/gpu_depth_feedback_563/{measurements,review}.json.
No motion/reset; scene remains563. Shared reserved calls4427. Next integrate
bounded sensor queries in the actual decision loop and obtain contact-region
geometry rather than more unstructured RGB-only closures.

563 INSPECTION: review of5cm open upward retreat chose HOLD (possible catching,
unresolved fingertip separation); no motion executed. Shared count4425 after one
additional review. Worker state remains563. Current wrist depth sampled at three
operator-selected visible shroud pixels gives z~.143m and y~-0.330m, versus nominal
pinch center z.15145/y-.36126m; closing axis nearly world+Y. Thus visible surface
is29-32mm off pinch center along closing direction and~8mm lower. This suggests
lateral alignment is unresolved, not just depth. Samples are ONE surface, NOT
card center/thickness or a motion command. Full numbers/provenance in
docs/evidence/gpu_enhanced_release/surface_audit_563.json. Next localize opposing
surfaces or obtain a view supporting distinct retreat; do not blindly shift32mm
or repeatedly close. The center-only grasp prompt is overly restrictive for
diagnosis; visible off-center surfaces can constrain geometry without pretending
the occluded grasp midpoint is measured.

OPEN-STAGE DWELL FIX PREPARED: conservative open-hand stages now terminate after
the ramp reaches its endpoint and4consecutive stable samples meet existing pose
tolerances, <=0.5mm/0.002rad per-step motion, aperture>=.99 and aperture change
<=.001. No camera/pass-through early exit; closure/loaded dwell unchanged.
An aperture that remains half-open cannot qualify an open-stage arrival.
Metadata labels this revision.307tests pass: fixture open hold4vs64actions,
fixture ramp42vs64; NOT new physical timing evidence. Current live worker88111
has NOT been reloaded, so563still uses the old controller. Preserve that scene;
load this change on the next fresh worker, not by unsafe in-process replacement.
This addresses observed unnecessary open-stage dwell, not grasp alignment.

RECOVERY UPDATE:533 legal-depth centerline audit found left9depth-edge/8occluded,
right17occluded, wrist4edge/10occluded/3surface-consistent samples (17per view).
These nominal centerline samples do not identify pad contact or object identity.
Fresh grasp localization review returned inspect: central top patch obscured.
Separate Astra visual review supported bounded open-in-place, not lift/closure.
Executed exactly30conservative guarded actions at CURRENT measured hand pose;
arrived563,2.427mm/.00590rad error,2sim/14.174wall seconds, aperture0.995887.
Image shows card still apparently supported. No verified grasp/recovery success.
This is a distinct operator-scoped model-reviewed release, NOT autonomous Direct
continuation or native FLUX behavior. Current worker88111/8774 holds563. No lift,
retreat or reset. Next obtain a less-occluded legal view or supported retreat
before selecting a depth-grounded grasp point; do not repeat vertical closure.
Scripts prepare_release_review.py/run_reviewed_release.py record this bounded
path, requiring exact review/current observation match and no automatic retry.
Evidence: docs/evidence/gpu_enhanced_release. Full sensor capture and audit remain
in runs/gpu_enhanced_533_sensor and runs/gpu_enhanced_533_visibility.json.
Two additional settled visual review calls; shared reserved count4424.

CONTACT CONTINUATION RESULT (supersedes current120 below): same episode now533,
worker88111/8774, STOPPED by contact tracking guard. Do not automatically retry,
reset or lift. Across four bounded segments:10GPT calls,533actions,35.533sim
seconds,342.085total segment wall seconds,$0.71696875. No verified grasp or native
success(score0). First continuation120->312:7cm descent,closure,3.5cm lift test;
card stayed supported while fingers rose (failed capture). Recovery312->504:
reopen/lower5.5cm,close,then reopen/lower another2.5cm after model recognized weak
engagement. At504 model chose stationary closure;29actions later guard stopped
at10.991mm hand deviation and0.02713rad rotation error. Do not infer collision
cause or secure grasp from this alone. Terminal image/result in
docs/evidence/gpu_enhanced_contact; full traces in runs/gpu_enhanced_direct_a_
{next3,recovery3,contact3}_20260930. Contact trace/image hashes verified.

Next: inspect current legal RGB-D/pad geometry to establish contact alignment
and a distinct supported recovery; not repeated blind vertical closure or wider
guard. RGB-only Direct has now exercised actual contact and failed capture,
while local tracking/free-space execution worked. This is not a final model
ranking. Depth was recorded but absent from Direct inputs. Conservative local
stages always consume64actions even at a stationary closure: code inspection
shows stable early-exit applies only to smooth paths. Fix that separately with
gripper-state settling semantics, not by blindly shortening contact dwell.
Shared reserved count now4422; all10reported costs settled by private launcher.

FIRST INTEGRATED LIVE RESULT: enhanced Direct-A, Astra Flex medium,3decisions,
all3fast EEF destinations arrived without guard stop/rejection.46+41+33=120actions,
8.0sim seconds,88.099total wall seconds; summed execution51.030s and model25.533s.
Endpoint errors0.298/0.338/0.385mm. Model cost$0.09263375. Motions include17cm
lateral,15cm descent, then about11cm combined lateral/descent, fixed orientation,
open grip. Final inspected right view shows gripper above card, not contact/grasp.
Native score0, success false; stopped at decision budget, NOT a failed motion.
This is integrated approach/controller evidence, not completed manipulation or
a matched model comparison. Legal inputs were RGB/proprioception/FK/receipts;
depth recorded but NOT supplied to this Direct policy. No hidden object state.
Source: runs/gpu_enhanced_direct_a_first3_20260930; public result and terminal
image in docs/evidence/gpu_enhanced_direct_a_first3. Current worker88111/8774,
episode8838a36a428c40c38aa6270f759398e4:120. Next bounded continuation from current
observation with prior execution memory toward alignment/contact; no reset.
Old86507 retired after246MB checksum-verified local backup at
runs/gpu_fast_ff_full_backup (SIGTERM lingered, exact-PID SIGKILL). Other scenes
untouched. Shared reserved call count advanced4412to4415; re-read before next call.

Launcher/target-limit continuation: private `run_adaptive_direct_trial.py` now
supports `--enhanced-gpu` and port18774. This selects the enhanced task, both local
execution/fast-transit flags, Direct horizon1 and64actions per decision (actual
actions counted). Hybrid accepted joint horizon stays8/32. Shared paid ledger,
holds, route and per-trial caps are unchanged. Enhanced config matches aimed-wrist
camera geometry and allows20cm/0.30rad EEF destinations while keeping joint limits
unchanged; CLI rejects this config without local execution.307tests pass; launcher
help/import verified. No paid call or simulator motion yet. Host process inventory
still shows all six retained workers. Next preserve temporary qualification
evidence, retire only that worker, and launch a fresh enhanced GPU episode.
This supersedes the launcher/3cm pending statements below.

- Shared local execution IS connected to Direct-A/B and Hybrid EEF fallback
  (`c17093c`); explicit fast-profile selection is implemented (`a13a3c9`). The
  external review's claim that integration is absent is stale.
- Make `--local-eef-execution --fast-open-transit` the standard configuration
  for the next enhanced GPU task trial and matched enhanced comparisons. This
  is an experiment default, not a change to legacy baseline semantics. The
  private launcher still needs to expose these flags and proper action budgets.
- Keep the current automatic eligibility restrictions and conservative fallback:
  fast motion requires open measured/commanded grip and both hand endpoints
  >=0.30 m. This is NOT clearance certification or blanket qualification of
  lateral/rotational paths. Only unloaded vertical up/return has passed so far.
- Do not chase 10x or repeat generic speed sweeps. Finish launcher support and
  explicit enhanced destination limits (currently only3cm), then run the actual
  GPU approach/grasp loop. Qualify new motion dimensions as needed in that task.
- Next physical milestones: secure grasp, retained carry, correct insertion
  approach, seated placement. Verify each separately. Fast loaded carry remains
  a specific open item; the open-hand default does not fix slow payload transport.
- Follow useful integrated behavior with matched A/B/Hybrid, then predefined
  same-episode recovery and execution-memory reuse. Preserve native FLUX joint
  timing; do not call local-IK success FLUX success.
- Track calls per meaningful phase and simulated/wall time, not commit/test
  count. No additional physical success is claimed by this planning update.

Post-training suggestion: worthwhile as a separate research hypothesis, not yet
an authorized/started training run or a proven fix. First identify the exact
tau0/UnifoLM release, license, embodiment/action compatibility, usable task data,
training/evaluation recipe, held-out conditions and compute requirements. Do not
divert the occupied GPUs or mix task-trained results into the no-task-training
comparison. Current failures do not isolate policy distribution as their cause;
a negative training result would not isolate perception/contact as the cause.
Active camera inspection remains useful when observations are ambiguous; no new
camera architecture is needed before the integrated task trial.

Latest self-contained report:
[shared-execution handoff](RESEARCH_HANDOFF_LOCAL_EXECUTION_20260930.md).

## Historical Implementation and Experiment Notes

Speed target updated by user:5--10x free-space transit, not2x as the final goal.
Offline `transit_trajectory.py` now produces synchronized rest-to-rest quintic
translation/rotation, using5x/10x peak speed caps and explicit acceleration caps
(.45m/s2,1.2rad/s2). For30cm translation at10x, the planned duration is2.53s,
NOT the earlier1.3s constant-speed lower bound. This excludes tracking/settling.
One time law spans the full transit; do not restart it at intermediate logging
waypoints or reintroduce pauses. Offline bounds tests pass; live integration,
joint feasibility, braking/tracking and payload qualification remain incomplete.
Do not enlarge the old per-action ramp caps or relax tracking gates to enable
these profiles. Existing2x RPC profile is only the earlier qualification option.

User direction: focus on GPU installation, not RAM. Suspend RAM experiments.
Preserve historical trials as historical evidence, not matched comparisons.

## Immediate sequence

Policy integration added: `physical-exec run --local-eef-execution` uses guarded
local feedback for exactly one EEF destination; Direct-A deltas become absolute
targets through existing validation, Direct-B retains absolute targets. Hybrid
joint accepts still use native execution; EEF alternatives use local targets.
Requests/receipts retain source and proposal IDs, actual control actions consume
budget, nonarrival/guard stop terminates without retry, memory explicitly labels
destination versus low-level action count. Multi-target EEF decisions rejected
before budget truncation. CLI defaults direct horizon to1 in this enhanced mode.
This changes execution semantics and is NOT original upstream reproduction.
Current integrated mode uses CONSERVATIVE local motion and existing task limits;
fast-profile policy selection and larger admitted destination limits remain to
be explicitly configured/qualified. No live-model enhanced trial yet.

FEEDFORWARD PHYSICAL RESULT:5x passed12cm up/return in33+35=68actions,
4.533sim/29.313execution wall seconds. Endpoint errors0.336/0.216mm, no guard
stop. Compared with conservative209actions/13.933sim seconds:3.07x faster
including acceleration and settling, not5x elapsed-time speedup. Same GPU task,
camera config, seed and path;5x uses smooth whole-move paths and stable settling.
Relative to FAILED smooth5x without feedforward, fresh5x+feedforward passed.
[Up receipt](evidence/gpu_fast_ff/0_receipt.json),
[return receipt](evidence/gpu_fast_ff/1_receipt.json).

Then explicit10x qualification continued from successful returned68 without reset.
It stopped after8actions at76 by unchanged tracking guard; no return/retry.
[10x stop](evidence/gpu_fast_ff/10x_stop_receipt.json). Current worker86507/8774,
episode4d39db60cb234fbf899be392416bddea:76, retained. Failed old5x worker85321
archived locally under runs/gpu_fast5_full_backup and retired before fresh test.
Original five task/recovery workers untouched. No paid calls.

Stop speed tuning here for now:5x UNLOADED VERTICAL qualification is useful,
but arbitrary paths, rotations, lower workspace and loaded carry are NOT qualified.
Next use this result toward GPU manipulation, qualifying those aspects as needed.
Do not automatically continue from stopped76 or silently enable fast contact.

5x follow-up diagnosis: largest recorded joint-command increment0.018153rad,
below upstream0.06rad/tick clamp. Terminal command-minus-measured differences
include+0.03338rad joint4/-0.03142rad joint6. This rules against the per-tick
command-rate clamp as the observed limiter, not against actuator dynamics or
all possible internal constraints. Full measured joint history was not logged.

Prepared optional `--trajectory-feedforward` for5x/10x smooth qualification:
one world-frame planned increment from current to next trajectory sample is
added to outer feedback, never accumulated in the integral. Existing command
caps and tracking target/guard remain unchanged; feedforward becomes zero at
the trajectory endpoint. Capability checked before reset. Not loaded in85321
or physically tested yet; no claim it cures tracking lag. Test on a separate
fresh qualification episode, not an automatic continuation of the guard stop.

5x LIVE TEST NEGATIVE: integrated whole-move quintic profiles5x/10x with
four-sample stable arrival termination;276tests pass. Fresh worker85321/8774,
episode76c94f90d92e476f827641d75829d382:11. First12cm upward move stopped by
unchanged10mm tracking guard after11actions,0.733sim/4.904wall seconds.
Actual upward displacement20.302mm; moving-waypoint lag11.093mm. Receipt's
99.699mm position error is distance to FINAL target, not the guard error.
No return/retry/contact/10x test. Retain11. Previous qualification worker84047
retired after recorded success; original five recovery/comparison workers untouched.
[Receipt](evidence/gpu_fast5_11/0_receipt.json).
Next diagnose tracking bandwidth/feedforward for the fast trajectory, not widen
the guard or claim5x qualified. Current motion feedback is insufficient for this
tested path; this does not establish a robot hardware speed limit.

- Conservative anti-windup qualification COMPLETED on fresh GPU-task worker84047,
  remote8774/local18774, episode20e8a36447af44088fa373cf8782e9ca:209.
  Open-hand12cm up/return:40+64+41+64=209actions,13.933sim seconds,
  89.271execution wall seconds. Upper endpoint0.080mm, return0.074mm error;
  intermediate descent1.367mm. No guard stop/contact/paid call or retry.
  [Endpoint image](evidence/gpu_antiwindup_209/3_right.png),
  [return receipt](evidence/gpu_antiwindup_209/3_receipt.json).
  Unloaded/elevated only; not proof of lower-workspace or payload performance.
  Other five workers preserved. Current qualification worker retained at209.

- [ ] Free a simulator slot without losing current GPU recovery2813.
  RAM baseline726 recordings are backed up and checksum-verified; retiring a
  worker loses live physics state, not merely GPU cache. Retention decision pending.
- [x] Qualify anti-windup on an elevated noncontact GPU-condition trajectory.
  Use the prepared bounded ramp/return probe; no repeat after ambiguous execution.
- [ ] Qualify faster transit, starting with twice the current translation and
  rotation rates. Increase further only with measured tracking and stopping
  evidence. Preserve slower approach/contact rates; do not change arrival gates.
- [ ] Demonstrate a sensor-grounded GPU grasp, lift, carry and placement with
  boundary verification. No hidden poses or collision truth in control.
- [ ] Run the matched enhanced A/B/Hybrid comparison below. Record failure and
  cost, not just success; no indefinite microdiagnostics between conditions.
- [ ] Test actual same-episode recovery and execution-memory reuse after useful
  manipulation. Installation and recovery are separate outcomes.

## Shared execution contract

Direct-A retains incremental Cartesian decisions and execution-grounded memory.
Direct-B retains absolute EEF decisions and its history semantics. Both may use
a bounded local feedback executor that interpolates and monitors motion without
asking GPT at every control latch. Larger action horizons or decision semantics
are explicitly enhanced variants, not unchanged upstream reproductions.

Local execution may interpolate an authorized target, monitor proprioception,
and stop; it must not silently choose grasp targets, invent task phases, retry,
or supply hidden scripted task solutions. Count all low-level actions and time.
Decision boundaries remain fresh observations, contact/closure, verification,
unexpected deviation, and capped stage completion, rather than arbitrary pauses.

Hybrid retains the existing accept/edit/eef/stop semantics. Accepted FLUX joint
proposals remain joint proposals with their original time/action contract.
Do NOT convert these to endpoint IK or time-compress them without separately
qualifying that transformed policy variant. Edited/FK-derived EEF proposals and
GPT EEF fallback may use the same local executor as Direct. Log their provenance
and separate their contribution from native FLUX execution.

## Matched conditions and outcomes

Freeze task initial condition/seed, camera setup, legal depth availability,
model and reasoning effort, controller version, transit/contact profiles,
arrival/stop limits, assistance flags, and overall action/time/call budgets.
Keep each mode's intended memory semantics explicit; do not add demonstrations
to only one condition. Start with one bounded trial per mode, not a broad sweep.

Report grasp, retention, placement, native isolated evaluation and recovery
separately. Also report GPT calls per meaningful stage, tokens/cost, wall time,
simulated motion time, endpoint error, peak overshoot, guards and execution-source
action counts. A controller test or visually plausible endpoint is not success.

Current status: plan adopted, execution integration and fast physical
qualification incomplete. Anti-windup is tested locally, not live-qualified.

Prepared speed profile: `elevated_open_2x`,45mm/s and0.12rad/s, versus default
22.5mm/s and0.06rad/s. Explicit request only; requires measured/commanded open
gripper, both endpoint heights>=.30m, tracking guard, and cadence<=1/15s.
Camera moves are excluded. These are experiment scope checks, NOT clearance
certification. Default/contact behavior unchanged. Worker metadata advertises
profiles; runner rejects old workers before reset. Run the ramp/return probe
with `--motion-profile elevated_open_2x` only after conservative qualification.
Not deployed or physically tested;267tests prove neither physical tracking
performance nor grasp retention. Larger rates remain deferred.
