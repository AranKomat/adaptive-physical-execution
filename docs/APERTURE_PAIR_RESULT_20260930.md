# Matched aperture result

## Outcome

Two fresh seed0 episodes used the same cameras, measured target, controller,
approach, closure budget and upward-lift compiler. Native grasp assistance was
ON. No paid calls were made. These were operator-directed tests, not autonomous
task completion.

| Commanded opening | Closure error | Final hand error | Measured hand rise | Visual result |
|---|---:|---:|---:|---|
|0.3|0.589mm|4.573mm|225.7mm|Card retained and lifted clear of support|
|0.0|0.214mm|0.172mm|230.5mm|Hand rose; card stayed on support|

Both pass the prospectively declared final lift motion bounds of10mm and0.03rad.
Only0.3 passes visual retention. The0.3 raw receipt remains a strict3mm
controller nonarrival; the0.0 raw receipt is a strict arrival. This demonstrates
why hand endpoint precision is not the same as grasp success.

The10-stage declared approach sequences are exactly equal. Closure requests
differ only in `gripper_open` and episode-specific `observation_id`. Both close
from step330 and finish at394; both lift schedules execute181 actions and end
at575. The compiler uses each measured post-closure pose for interpolation, so
intermediate lift coordinates differ slightly as a consequence of closure;
the sensor-derived final target and compilation rule are identical.
Measured post-closure normalized apertures were0.37949 and0.12183 respectively,
not the commanded setpoints. Neither readback by itself proves capture.

## Interpretation

For this specific setup, the aperture intervention changed the physical outcome.
It is now a demonstrated contributor, not merely a suspected confound. It does
NOT establish that all earlier Direct failures were caused by aperture: their
grasp positions also differed. Nor does it establish ordinary frictional grasp
quality. Native assistance uses aperture/stall/proximity conditions, and this
comparison does not isolate assistance eligibility from contact mechanics.
No privileged latch/site data was used to select targets or commands.

Do not run an aperture sweep, force another lift, or debug the4.573mm residual.
Next integrated attempt should expose this labeled prior experience to the
planner, preserve explicit continuous-aperture selection, and require visual
retention before carry/insertion. Do not silently clamp model closes to0.3.
If Direct and Hybrid are compared, give both the same evidence and action
semantics; this experience-conditioned result must remain distinct from zero-shot.
Full installation and recovery remain unachieved; no autonomous phase completed.

## Evidence And State

Public protocol, code fingerprints, requests, receipts, images and independent
visual reviews: [paired evidence](evidence/aperture_pair_20260930/).

-0.3 episode: `d6b57bcf034945eca22c4f6f26a90602:575`; worker96266 retired
 after critical-data backup and checksum verification. Remote recordings kept.
-0.0 episode: `e086f25bf69249db8d3f0a366cddf36d:575`; worker98214/8772 remains
 live, empty hand elevated. No further commands issued.
-Older reference full1.8GB recording backup completed and passed rsync checksum
 comparison at `runs/gpu_aperture_reference_full_backup`.
-Both new conditions have local critical backups (final RGB-D/calibration and
 command journals), plus local plans/receipts/review images. Their complete
 per-step recording trees remain remote, not fully backed up locally.
-Budget-stopped Direct scene92546/8774 at196 remains untouched; ceiling$85,
 unresolved holds retained, no new paid reservations.

Local run names use `gpu_aperture_pair03_*` and `gpu_aperture_pair00_*`.
