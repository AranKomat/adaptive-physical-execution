# Retained grasp comparison and next experiment

## Matched Pair Completed

Fresh prospectively assessed pair:0.3 retained/lifted the card;0.0 left the
card supported despite a clean hand lift. Both passed10mm/.03rad final motion
bounds. Approach sequences identical, closure requests differ only in aperture
and observation ID. Assistance ON; no paid calls. Full result and next action:
[APERTURE_PAIR_RESULT_20260930.md](APERTURE_PAIR_RESULT_20260930.md).
Do not repeat an aperture sweep or debug the old4.573mm residual. This replaces
the pending-comparison instructions below; historical receipts remain unchanged.

## Completion Criteria Correction

Following user feedback, a3mm precision endpoint is unnecessarily strict as
the completion criterion for this upward retention diagnostic. The existing run
remains a strict controller nonarrival, but its visible assisted lift is a
positive physical result, not a failed grasp. Do not erase either observation.

For the next matched pair, declare the same criteria BEFORE motion in both arms:
`run_sensor_carry.py --lift-diagnostic-completion --contact-tracking-guard`.
Only the final upward endpoint may complete within10mm translation and0.03rad
rotation, either on strict arrival or after the full64-action budget. Every
intermediate waypoint retains its original completion check. Guard stops,
aborted/rejected commands, missing/nonfinite telemetry and other terminal reasons
remain failures. No additional retry, longer budget or forced movement is added.
The runner restricts this option to at most four upward stages/23.1cm total,
at most1mm lateral adjustment, preserved attitude, and unchanged grip commands
through the existing compiler. It cannot be used for insertion or standoff.
Raw receipts remain untouched; a separate assessment records motion completion
and explicitly leaves grasp verification false until independent visual review.

Use fresh matched runs with these criteria, not a retry of the stopped live
episode. Require visible card retention/support clearance for the physical lift
outcome. Keep assistance ON/disclosed and cached-pixel legal-depth provenance.
Do not spend another diagnostic cycle solely reducing the old4.573mm residual.
The code and bounds passed335 CPU tests; no new physical run has yet exercised
this completion option. Earlier stop decisions below describe the old protocol.

## Latest Reference Result

The no-API reference run reached episode
`be30df64d12349588c2bfb0d0cad3fd1:575` on worker93658/8772.
Fresh legal depth at the cached pixel reproduced the reference surface point.
The guarded approach arrived at step330 (0.214mm position error). Visual review
supported an operator-scoped closure hypothesis, not a certified grasp.
Closure at0.3 arrived after64 actions (0.589mm error).

The upward trajectory passed three intermediate waypoints (39 actions each).
The last waypoint exhausted64 actions with4.573mm position error, exceeding
the unchanged3mm arrival threshold. Execution stopped without retry. Final
hand z was0.458636m versus target0.463198m. Both external images clearly show
the card held above the now-empty support. Thus visible assisted retention and
substantial lift occurred, but strict endpoint reproduction FAILED. No insertion
or autonomous success is claimed, and the0.0 condition was NOT run, as required
by the predeclared stop rule. Aperture causality remains untested.

Implementation detail: the existing carry compiler was reused for this upward
diagnostic; its internal `elevated_carry_*` name is not verification of capture.
It interpolates four waypoints from measured post-closure FK to the refreshed
reference endpoint, rather than replaying historical intermediate coordinates.
The current approach also includes updated open-hand settling. This is a
reference-style reproduction under current code, not a bitwise historical replay.
Any future matched pair must use this same compiler and approach in both arms.

Public receipts, source plans and before/after images:
`evidence/aperture_reference_20260930/`. Local run directories use the same
names. Live final state is preserved. No paid requests were made; the shared
$85 ceiling and all unresolved holds remain unchanged.

## Finding

The successful guarded fixed-fixture recipe and recent Direct-A trials do not
use equivalent grasp commands. They differ in aperture, position and lift
schedule. Therefore the failed Direct lifts cannot isolate a depth, perception,
or controller deficiency.

The reference is `guarded_full_lift_20261001_execution`: request10 closes at
world hand XYZ `[0.274712, -0.337201, 0.233198]` m with `gripper_open=0.3`.
Its closure passed at1.211mm error; final23cm lift endpoint passed at2.351mm.
This was operator-directed, cached-pixel-on-fresh-depth execution with native
grasp assistance, not autonomous installation. Endpoint receipts alone are not
grasp verification; historical visual retention evidence remains necessary.

| Direct trial | Opening command | XYZ difference from reference (mm) | Outcome |
|---|---|---|---|
| continue7 | 0.0 | +10.42, -11.11, +3.46 |25mm hand lift arrived; card did not follow|
| regrasp_guard9 | 0.0 | +20.61, -6.99, +1.16 |20mm lift budget-ended8.49mm short|
| fresh_grasp12_continue13 | 0.0 | -32.41, -2.77, +3.78 |first4mm lift arrived; second guard-stopped|

Opening is a continuous command, not a binary semantic grasp. The older pilot
also explicitly requested12mm finger position. A zero target can impose a
different contact load than partial closure, but no force measurements here
prove that this caused failure. The world-coordinate differences are cross-run
command differences, not measured errors relative to the object's current pose.

## Next Bounded Test

### Assistance Audit Before Execution

Pinned upstream `robobench/core/grasp_weld.py` uses the default Panda
`joint_sum` closure mode. `_gw_closure` computes measured finger-joint sum and
calls the fingers stalled when summed absolute finger velocity is below the
configured threshold. `step` also checks a site-specific aperture window,
pinch proximity and debounce. This is NOT a measured opposing-pad force test.
A quiet commanded aperture can affect this gate without establishing ordinary
frictional grasp quality. Neither opening command directly guarantees engagement.

Do not expose grasp-band coordinates, latch state or these site windows to
the controller. This source audit is an evaluator/methodology warning only.
Do not tune an aperture to a hidden band or disable the assistance silently.
The proposed0.3/0.0 comparison remains justified by retained commands, not hidden
geometry. Even a positive result must be reported as assistance-on behavior,
not proof of physically robust or real-world grip force.

No new aperture API is necessary: `scripts/probe_contact_stage.py` already
accepts `--opening` with a current reviewed candidate and tracking guard.
Use that existing control for the two conditions; preserve the selected opening
for the identical lift schedule. Do not add a silent default to Direct/Hybrid.

Live capacity inspection: GPU0 has848MiB free and GPU1 has2030MiB free; six
workers retain scenes. Do not launch a seventh simulator on these margins.
A user choice on retiring backed-up suspended RAM8772 has been requested.
Current GPU92546/8774 scene196 and other retained scenes remain untouched.

User subsequently approved RAM8772 retirement after backup and an increase of
the shared API ceiling to$85. The private launcher/ledger now accept$85 with
all unresolved holds retained. RAM backup is in progress; retirement requires
checksum verification first. This authorization is not a new experiment result.

Backup/retirement completed: all6,494 files in RAM8772's2.3GB recording tree
passed SHA-256 verification against the source manifest. Local backup:
`runs/ram_aimed_20260930_full_backup`; verification:
`runs/ram_aimed_20260930_backup_verification.txt`. Exact PID79506 was retired
after command-line identity validation. Original remote files retained; live
RAM physics state lost as approved. GPU1 free memory increased to9295MiB.
The independent reference-aperture worker is now being provisioned on8772;
GPU scene196 on8774 is unchanged. No aperture outcome yet.

Stop prompt-only centering sweeps. Run a simulator-only, no-paid-call matched
aperture comparison, separately labeled as an operator-defined diagnostic:

1. Preserve current worker92546 and its budget-stopped open-hand scene196.
   Use a separate worker after checking capacity and preserving any retired run.
2. Freeze current code, seed, camera configuration, controller, assistance,
   selected pixel rule, approach, closure budget and lift trajectory. Recompute
   targets from fresh legal RGB-D, never from privileged object state.
3. First reproduce the reference-style0.3 closure with the unchanged guard.
   Verify preclosure RGB-D geometry and independently observe retention. If
   reproduction fails, stop; do not attribute later differences to aperture.
4. In a fresh matched episode change ONLY closure/hold opening to0.0. Keep
   duration, trajectory and all abort conditions identical. No retry after
   guard/nonarrival and no forced lift after failed closure.
5. Compare command tracking, aperture readback, before/after RGB and actual
   support clearance. A guard stop is an outcome, not an instruction to increase
   force or disable the guard. One pair is diagnostic, not a success-rate claim.

If aperture matters, expose continuous aperture semantics to Direct and Hybrid
equally; do not silently replace every model close with0.3. If it does not,
test target placement next while holding aperture fixed. Neither result alone
completes installation, autonomous recovery or matched policy comparison phases.

## Reproduction

`scripts/compare_retained_grasps.py` reads only retained JSON and emits the
comparison with SHA-256 source fingerprints. It refuses to overwrite output and
contains no simulator/API client. Public numeric evidence:
`evidence/depth_contact_20260930/grasp_command_comparison.json`.

The retained-command analysis itself made no paid calls or robot commands.
The subsequent operator diagnostic is tracked above. The user-approved shared
reservation ceiling is now $85, with unresolved holds retained; the prior paid
episode remains stopped.
