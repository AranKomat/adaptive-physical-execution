# Retained grasp comparison and next experiment

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

No paid calls or robot commands were made for this comparison. The shared$75
reservation ceiling remains unchanged; current paid episode remains stopped.
