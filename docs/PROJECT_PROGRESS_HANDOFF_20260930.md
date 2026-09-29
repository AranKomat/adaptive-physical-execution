# Adaptive Physical Execution: project progress and research handoff

Snapshot: September 30, 2026, JST. Covers the current project's initial roughly
ten-hour work period as requested by the user, not the older BEHAVIOR project
or the entirety of the earlier EmbodiedSWE coding-agent experiments. Durations
below are measured per experiment; the ten-hour description is approximate.

## Latest continuation (supersedes the older live-state section below)

Continuous-transit fixed-fixture lift completed: 693 vs 896 actions, 46.200 vs
59.733 sim seconds, 310.724 vs 400.042 execution seconds. Same measured targets;
cached pixel templates declared. Strict final error 2.351 mm; separate review
confirmed clear_lift, costing $0.0194525. Grasp assistance remains on. Video:
`docs/evidence/smooth_lift_20260930/lift_1x.mp4`.

The integrated camera then moved while holding the arm: eye readback passed,
arm error 1.021 mm, but the view is gray/occluded (finite median depth 10.45 cm).
Useful socket observation remains unresolved; no carry/insertion followed.
Current live worker session 5966, loopback port 18767 -> remote 8767; current
episode/observation `13b72700c14b45ecaca1f7e32103ae78:757`. The prior episode was
ended explicitly to load the new worker; do not attempt to resume its IDs.
New protocol/evidence: `docs/SMOOTH_LIFT_20260930.md`. Next improve the camera
view in this held episode using legal geometry, without repeating the lift.
Latest shared reserved-call count: 4,357; recheck ledger before any new call.

Repository: https://github.com/AranKomat/adaptive-physical-execution

Local checkout: `/Users/macbookpro/Developer/random/gpu/adaptive_physical_execution`.
Primary checklist: `/Users/macbookpro/Developer/random/gpu/GPT6_ADAPTIVE_PHYSICAL_EXECUTION_HANDOFF_20260929.md`.
This report summarizes current evidence rather than treating every historical
"next" item in older reports as still pending.

Latest follow-up: the paused close-target trial has now achieved clear assisted
suspension in the integrated worker. All strict endpoints passed. Three fresh
calls including subsequent carry review cost $0.072945. Carry review requested
inspection because the destination socket is occluded; no carry was issued.
See updated live state below and `docs/CLOSE_TARGET_20260930.md`.
One later inspection-planning call declined a <=5 cm non-descending hand move;
no motion. Four-call episode total is now $0.0995975. Independent camera control
exists in the older pilot but must be ported to the integrated worker before a
new camera view can be commanded; a fresh process would be required to load it.
Update: this port is now implemented and covered by 183 CPU tests, but is not
loaded in the current worker or live-qualified. See
`docs/INTEGRATED_INSPECTION_CAMERA_20260930.md`. The suspended episode remains untouched.

## 1. Executive assessment

**We have not completed the main objective.** No nonprivileged autonomous PC
assembly, successful adaptive recovery, or demonstrated memory benefit exists.
FLUX has not produced a verified grasp in the tested PC-assembly condition.

**There is real physical progress, not only software plumbing:**

- An earlier successful program completed the full GPU installation in a
  separate privileged replay: seated, released, and hand clear.
- A sensor-targeted, operator-defined native DiffIK recipe achieved controlled
  assisted lift and elevated carry with approximately 2 mm endpoint errors.
- A later sensor-grounded insertion attempt reached its commanded pose but did
  not seat the card. This separates execution accuracy from task success.
- Same-episode Hybrid-to-local correction now executes, but its grasp attempts
  have produced partial contact rather than secure suspension.
- We found and fixed actual integration faults, notably stale wrist extrinsics,
  a translation-only pose ramp, and a wrist camera that excluded the nominal
  pinch region. These were not just model-prompt tweaks.

The current bottleneck is **reliable task-relative geometry and contact**, plus
transferring demonstrated local execution into model-directed stage decisions.
It is not established that Astra is too weak, that all IK is broken, or that a
different general architecture is required. Conversely, accurate endpoints do
not establish that the chosen grasp or insertion target is correct.

Progress has been uneven: useful motor/sensor capabilities were established,
but too much work subsequently accumulated in serial grasp/view/threshold
diagnostics without completing another physical task phase. The next work
should close the integrated grasp-to-alignment loop, not expand those sweeps.

## 2. Objective and current approach

Original objective: combine GPT reasoning, an existing action policy, and
experience memory to solve difficult EmbodiedSWE PC assembly tasks and recover
when the physical state changes, without task-specific training or privileged
object-state inputs to control. GPU installation is first; RAM and combined
GPU+RAM follow only after the individual task works.

Three implemented experimental modes:

1. Direct-A: single-arm port of RoboICL-style incremental Cartesian actions and
   anchored history.
2. Direct-B: single-arm absolute-EEF reference port with fuller history.
3. Hybrid: FLUX proposes joint actions; GPT reviews bounded prefixes and can
   stop or request other actions.

User priority changed after Direct proved call-inefficient: aim for **one to a
few GPT calls per meaningful stage**, with bounded local feedback doing the
motion. Direct remains a reference or exceptional recovery path, not a reason
to spend twenty model calls just reaching above a component.

Current local-stage recipes are operator-authored. They are useful test tools,
but must not be relabeled as autonomous model-authored recovery. The final
goal still requires the model to select and adapt meaningful stages from
observations, execute them, verify effects, and recover when needed.

## 3. Runtime and experimental conditions

- Scene: EmbodiedSWE PC GPU assembly; single Franka/Panda; mostly seed 0.
- Native simulator grasp welding/assistance is **ON**. All successful captures
  reported here are assisted; no unassisted hardware competence is established.
- External swept clearance is unknown. These are explicitly bounded simulator
  experiments, not collision-certified or hardware-safe procedures.
- Control inputs: RGB, idealized simulator RGB-D when enabled, calibrated camera
  transforms, robot joints and EEF pose. Simulator object transforms, hidden
  grasp flags and native scoring are excluded from nonprivileged control.
- Depth is a sensor-style observation, not an object-state query. It is still
  idealized simulation depth, not validated real RGB-D sensing.
- GPT: `openai/gpt-6-astra`, pinned `openai/flex` provider route, normally medium
  reasoning; one bounded high-reasoning follow-up also ran.
- FLUX: standalone DROID `variants/gd-fp8r`; camera/embodiment distribution match
  to this simulator remains unproven.
- Current rental has two RTX 4090s: GPU 0 for simulation, GPU 1 for FLUX.
  First standalone FLUX probe peaked near 21.0 GiB allocated / 22.2 GiB reserved;
  Isaac used about 7.3 GiB after capture. Simultaneous residency on one 24 GB
  device was not a credible budget. These are single-run figures, not a memory
  optimization study.
- Source revisions are pinned in `upstream.lock.json`. Native RoboICL and
  GPT-as-Policy benchmark reproductions have NOT been completed; these are ports.

## 4. What ran and what happened

### Infrastructure and initial qualification

The delivered CPU harness includes typed observations/actions/receipts, stale-ID
checks, FK/IK and joint continuity checks, authenticated workers, trace integrity,
explicit API budgets, anchored memory helpers and evaluator separation.

Real Isaac capture, robot FK and FLUX inference subsequently ran. Fixed a URDF
parser error that rejected a legitimate zero axis on a fixed joint. Installed
the missing renderer library on the initial host. Startup exceptions are now
reported before cleanup; Isaac shutdown can still hang operationally.

FLUX's raw gripper output slightly exceeded its declared range. Raw values were
retained, with explicit bounded conversion experiments; no blanket silent
clipping. A 0.446% overshoot fit the opt-in 1% tolerance, a later 1.311% overshoot
did not. Subsequent admitted Hybrid execution is real, but this does not qualify
arbitrary outputs or prove task competence.

### Direct-A, Direct-B, and reasoning effort

| Trial | Calls | Control actions | Sim / wall seconds | Reported API cost | Physical result |
|---|---:|---:|---:|---:|---|
| Direct-A, medium | 23 | 90 | 6.0 / 258.18 | $0.74780350 | No verified lift; native score 0 |
| Direct-B, medium | 20 | 58 | 3.867 / 208.75 | $0.55426050 | No verified lift; native score 0 |
| Direct-A, high | 20 | 71 | 4.733 / 406.45 | $0.66809500 | No verified lift; native score 0 |

Both medium controllers approached, attempted grasps, recognized missed lift
tests, and changed lateral/depth targets. Failure recognition is promising but
not successful recovery. High reasoning did not rescue this bounded trial.
Budgets/history/action horizons differ, so these are not a fair final ranking.
An earlier interrupted A run used 12 calls / 53 actions / $0.301375 before a
request-size bound stopped it; that negative operational result is retained.

A receipt audit found median chunk-end position errors around 8.6/11.0/14.8 mm
for A/B/high. This motivated spatial grounding and local feedback rather than
more reasoning-level sweeps. RGB-only target error and actuator tracking error
were initially confounded.

### Control/reference comparison and first useful physical effect

Matched free-space reaching at 15 Hz: upstream DiffIK algorithm reached within
2.521 mm in 32 actions; integrated iterative IK reached within 2.220 mm in 31.
This did not show a gross calibration disadvantage, but says little about contact.

A separate unchanged privileged reference completed installation in **1,859
actions / 570.834 wall seconds / zero model calls**, including release and
hand clearance. This proves the tested scene/controller can complete the task,
not that our nonprivileged agent can infer the necessary geometry.

Sensor-targeted OSC captured/lifted but lost orientation: final angular error
2.591 rad. Native DiffIK preserved attitude but initially finished about 99 mm
short of the lift target. A bounded translation integral plus larger command
cap then achieved:

- Lift: 1.945 mm / 0.02094 rad endpoint error.
- Elevated carry: 1.661 mm / 0.01778 rad endpoint error.
- Seven arrival checks passed; full episode 3,130 actions / 65.208 simulated
  seconds / 1,116.920 wall seconds, including planning and transfers.
- Three fresh review calls cost $0.0686325; earlier grasp pixels were reused.
- Images showed the card above an empty support and later above the chassis.
  Post-control evaluation: held=true, task=false.

This is the strongest nonprivileged sensor-targeted physical result so far,
but uses cached pixel templates, an operator-defined sequence and grasp assistance.
Native pilot cadence was 48 Hz; the integrated worker is 15 Hz. Do not present
these as an isolated single-variable controller comparison.

### Socket visibility, inspection and attempted insertion

An overhead camera condition localized a candidate socket before grasp. After
carry, hand/card occlusion prevented reliable mating-feature correspondence.
Historical context helped the model remember the socket but did not prove
current alignment.

An independently movable idealized inspection camera was qualified: the first
Fabric pose route failed, the pinned USD route worked. The camera has no collision
body; this is not a mechanically qualified head/arm camera system.

Post-carry inspection then supported two closer reviewed approaches and one
contact-intended attempt. Final hand error was **1.960 mm / 0.01236 rad**, yet
native seated=false and held=true. No release or successful assembly. Four
fresh calls cost $0.08531625. The episode used 4,678 actions / 97.458 simulated
seconds / 1,250.107 wall seconds, including long command waits.

Higher-detail pre-grasp imagery improved sampling from roughly 2.62 to 0.80
mm/pixel and yielded three consistent socket-housing rail samples (about 0.626
mm local depth spread). The actual gap/key and corresponding connector ends
remained unresolved. A paired-rail review still requested inspection. This
branch was stopped rather than pressing downward harder.

### FLUX Hybrid and same-episode local correction

| Trial | Executed motion / calls | Outcome |
|---|---|---|
| First Hybrid | 24 joint actions, three reviewed prefixes; $0.2037775 | Plumbing passed, no grasp |
| Clarified Hybrid plus continuation | 88 FLUX actions, 8 calls; $1.08917125 | Closed/lifted hand, card stayed supported |
| Revised uncertainty rule | 76 FLUX actions, 7 calls; $0.76792875 | Reviewer caught premature closure/transport and stopped |
| Corrected Hybrid + local recipe | 75 Hybrid actions, then 896 local actions; 10 total calls, $0.97526375 | Accurate endpoints, partial card lift/tilt, not secure capture |

Important fixes: distinguish EEF-command limits from FK displacement of joint
proposals; remove an unjustified fixed two-uncertain-chunk cutoff; cap local
stage actions before execution to avoid a post-motion receipt construction
failure; replace a translation-only ramp with a bounded position-and-rotation
ramp. None of those fixes establishes FLUX's PC-assembly competence.

The successful local correction execution still selected an imperfect grasp.
Maximum endpoint position error was 1.596 mm, while visual review correctly
classified the card outcome as partial_contact. Accurate motion is not enough.

### Wrist camera, closure and current grasp work

Robot-only projection showed the nominal closing region entirely outside the
original wrist image: 0/17 sampled points in frame. An opt-in camera aim toward
the nominal pinch center brought 17/17 into frame. The robot-local 0.1034 m
pinch offset is a convention, not a qualified contact-pad mesh model.

An exploratory closure initially missed strict orientation arrival (0.04097 rad
versus 0.03). A fresh angular-integral trial subsequently passed strict closure:
1.759 mm / 0.01035 rad. Its one 5 cm lift finished at 4.714 mm / 0.03341 rad:
within predeclared exploratory bounds, not strict precision arrival. A nine-image
Astra review ($0.02803375) returned partial_contact, not secure suspension.

Object tilt and hand tracking error are different. A 25-degree-slanted card can
still be securely grasped; tilt alone is not failure. The relevant evidence is
support clearance, retention and later task-specific alignment. We did NOT
change the hard worker orientation abort to 25 degrees. Exploratory contact
completion is at most 10 mm / 0.15 rad with all requested actions executed;
raw strict receipts and hard stops remain unchanged.

Comparison with the successful pilot exposed confounds: the recent target is
about 31 mm laterally different, and lift height was only 5 cm rather than 23 cm.
The successful pilot also refreshed the target from the wrist after approach.
These differences motivate the current close-range refresh trial, not another
threshold-only experiment.

## 5. Phase status: no inflated completion claims

The current project's original plan has phases **0-7**. Do not confuse it with
the older BEHAVIOR project's 0-14 sequence.

| Phase / deliverable | Status | Missing evidence |
|---|---|---|
| 0: scope and contracts | Complete for initial scope | Later execution refinements are explicitly labeled |
| 1: unchanged upstream qualification | Partial | Native RoboICL/GPT-as-Policy benchmark rollouts |
| 2: EmbodiedSWE adapter | Partial | RAM and broader end-to-end qualification; PC GPU works |
| 3: Direct-A | Partial; negative task trials | Successful task/recovery, native parity |
| 4: Direct-B | Partial; negative task trials | Successful task/recovery, native parity |
| 5: Hybrid | Partial; real joint execution and failed grasps | Reliable grasp, model-directed successful correction |
| 6: FLUX substitution | Partial; inference and admitted execution | Robust boundary/distribution/task qualification |
| 7: memory | Software exists | Executed physical benefit versus no-memory baseline |
| Nonprivileged full GPU installation | Not achieved | Seating, release and independent/native verification |
| Recovery from changed physical state | Not achieved | Model-detected failure followed by successful correction |
| RAM, combined GPU+RAM | Not meaningfully evaluated | Individual task success before combined sequence |
| Successful-trace reuse/new layouts | Not evaluated | First successful nonprivileged trace, then transfer |
| Matched A/B/C comparison | Not complete | Same setup, budgets, conditions and repeated trials |

Videos and component tests exist; neither substitutes for these task requirements.

## 6. Current paused episode and exact continuation

`close_target_20260930` has now completed **896 actions**: 448 approach and 448
descent/closure/lift actions. All strict arrival checks passed. Final lift error:
**0.817 mm / 0.002588 rad**. A fresh target call selected a current-image pixel,
depth was measured, and independent review returned clear_lift. A third call
requested inspection before carry because the destination socket is occluded.
Execution wall time 400.042 s; simulated time 59.733 s; three-call cost $0.072945.

- Episode: `c3145c96f5344d6fa999b5b506de89ae`.
- Last observation: `c3145c96f5344d6fa999b5b506de89ae:896` (card suspended).
- Local worker URL: `http://127.0.0.1:18767`; remote port 8767.
- Server shell session at this snapshot: 30978; approach and grasp clients exited 0.
- Local approach evidence: `runs/close_target_20260930_approach`.
- Remote recordings: `/workspace/adaptive-physical-execution/runs/close_target_20260930_recordings`.
- Protocol: `docs/CLOSE_TARGET_20260930.md`.

Next operator should verify the live observation and process, not assume these
handles remain valid. One episode per worker; do not reset this paused worker.
Do not restart a motion on a timeout without checking execution state.

Planned continuation: obtain an informative legal destination view while
preserving suspension, then localize corresponding features before carrying.
The independently movable camera exists in the older pilot; it is not yet an
available camera-control endpoint in this integrated worker. Do not restart
and replay the grasp merely to repeat a static-view guess. No automatic carry
on the inspect response, no privileged destination coordinates, and no release
without observed support. This remains exploratory, not autonomous recovery.

## 7. Recommended next sequence

1. Preserve the now-demonstrated integrated assisted suspension; do not repeat
   its approach or another grasp/controller sweep.
2. If suspension is established, preserve observed hand/card geometry and
   obtain corresponding connector/socket features before descent. A top-surface
   pixel is neither a grasp center nor an insertion pose.
3. Attempt one bounded sensor-grounded alignment/seating/release sequence only
   from adequate observed geometry. Verify actual effect, not endpoint accuracy.
4. Once useful stage execution works, expose it to model-selected, observation-bound
   decisions. Demonstrate one actual recovery without operator-writing the next
   correction for the agent.
5. Then compare matched Direct/Hybrid routing and memory/no-memory execution;
   extend to RAM and changed layouts after initial success.

Stop repeating prompt-only FLUX approaches, high-reasoning rescues, tiny unloaded
IK tests, or near-identical static-camera searches without a new discriminating
question. Do not relax unknown clearance into a safety claim or import privileged
reference geometry to manufacture a nonprivileged success.

## 8. Costs, speed and practical limitations

Costs above are per documented trial, not an audited project grand total. They
exclude rental charges, prior projects and unresolved API holds. The shared
private ledger is authoritative; preserve its $75 ceiling and unresolved holds,
including the older $1 routing-error reservation. Last completed review brought
the reserved-call count to 4,356; recheck before the next request.

Small stage reviews often cost cents, whereas history-heavy Direct loops used
many calls without task completion. Lower call count is useful only if physical
progress follows. Current local recipes can execute hundreds of actions with
no intervening model call, but task-level efficiency is not yet demonstrated.

Motion appears slow for several reasons: conservative target ramps (0.0225 m/s
translation and 0.06 rad/s rotation in the local worker), fixed settling/action
budgets, simulation/render/depth-recording overhead, and paused wall time during
reasoning/transfers. The latest 64-action stages represent 4.267 simulated
seconds but take roughly 27-30 wall seconds. Some older inspection videos are
explicitly 0.25x simulated playback. Do not infer physical speed from video
duration or attribute all wall time to GPT latency. No rigorous latency
optimization or safe higher-speed qualification has been completed.

## 9. Artifacts and operational handoff

Public summaries and selected evidence are under `docs/` and `docs/evidence/`.
Full raw `runs/` recordings and API audits are generally ignored by Git; a push
is not a full data backup. Previous sensor lift/carry and contact-integral
recordings are retained locally. Current standoff RGB/robot state and selected
depth/calibration are preserved locally (export passed exact observation-ID and
RGB checksum checks); the full current recording stays
on the GPU host until a complete sync is performed.

Key reports, in reading order:

- `docs/DIRECT_COMPARISON_20260929.md`
- `docs/REFERENCE_TRANSFER_20260929.md`
- `docs/SENSOR_DIFFIK_PILOT_20260929.md`
- `docs/POST_CARRY_CONTACT_20260930.md`
- `docs/HYBRID_GRASP_ATTEMPT_20260930.md`
- `docs/HYBRID_POSE_RAMP_20260930.md`
- `docs/WRIST_AIM_20260930.md`
- `docs/CONTACT_INTEGRAL_20260930.md`
- `docs/CLOSE_TARGET_20260930.md`

GPU host: `ssh -p 45579 root@76.71.203.193`.
Remote checkout: `/workspace/adaptive-physical-execution`.
Original simulator port 8765 and FLUX port 8766 are separate from the current
temporary worker. Do not terminate unrelated services or the user's CPU workload,
reboot, or stop/destroy the rental as part of routine experiment cleanup.
Credentials are private; never put tokens, keys or `.env` contents in this repo.

CPU regression command from the checkout:
`env PYTHONPATH=src ../internal/physical-ai-lab/.venv/bin/python -m pytest -q`.
Latest result: **179 passed**. Tests cover software contracts, not task competence. Revalidate current state
before resuming; this is a snapshot, not a promise that a process remains live.

## 10. Bottom line

The project has demonstrated enough physical capability to justify continuing:
sensor-derived targets can drive assisted grasp/lift/carry, local control can
track accurately, and the task is solvable under a privileged reference.
But it has not yet demonstrated its central proposition: efficient,
nonprivileged, model-directed assembly and recovery. The next milestone must
be an integrated physical success, not another collection of passing checks.
