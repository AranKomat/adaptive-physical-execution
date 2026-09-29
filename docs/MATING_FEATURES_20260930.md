# Separate mating-feature localization

Continuation of aimed_lift_20260930, same held episode. Reobserved 1213 without
motion before a new observation-only feature inventory. It allows connector
and socket to be independently visible/occluded; rough housing-axis localization
does not require a visible key or imply insertion approval.

Astra reported connector occluded and socket axis visible, with right pixels
[287,244] and [330,226]. First selected 3x3 depth patch fails the unchanged
10 mm spread check; second passes (8.899 mm spread). Nearby patches within
two pixels include continuous surfaces but can land on different rail faces:
do not silently substitute these or certify a measured axis. This separates
semantic recognition from depth support and from mating alignment.

Next predeclared inspection: same arm/grip, 64 holds, eye [0.80,-0.05,0.50],
gaze [0.47224,0.02803,0.2695]. The gaze is a viewing hypothesis from previous
legal socket/connector measurements and executed carry, not a newly measured
connector pose. It seeks a lower PCB-side view under the shroud. Translation
and angular path preflight pass unchanged limits. A closer candidate exceeded
angular speed and was rejected offline; no command was sent for it. Unknown
clearance remains explicit. No descent, release or automatic retry.

At 1277 the PCB-side view exposes the lower contact strip. Independent feature
review marks both axes visible, but one sample per feature fails the unchanged
depth check. Valid connector sample [338,224] measures
[0.5223449244,0.0285393071,0.2669298153]; valid socket sample [407,349] measures
[0.4564232327,0.1253566159,0.0293319033]. The latter differs from the earlier
carry target by about 9.7 cm in y. Projection of the original carry target into
the current calibrated camera yields [320.00,375.17], BELOW the 360px image.
This suggests a neighboring-slot switch, not established target continuity.

Next: retain eye [0.8,-0.05,0.5], aim lower at [0.47224,0.02803,0.15] over
64 holds so the original slot region enters frame. Preserve arm/grip. Review
with explicitly labeled historical carry image/selection and require identity
association or correction, not arbitrary socket discovery. No descent/release.

## Outcome at 1341

Camera aim completed in 64 actions / 30.709 wall seconds, arm hold error
0.860 mm / 0.002091 rad. Eye [0.8,-0.05,0.5], gaze [0.47224,0.02803,0.15].
History-aware review associated the CPU-adjacent socket with the earlier carry
target. Both current socket samples pass the unchanged 3x3/10mm depth gate:

- [309,224]: [0.4329796247,0.0252634625,0.0430239368] m; spread 1.913 mm.
- [319,256]: [0.4726228136,0.0268801192,0.0377966154] m; spread 1.749 mm.

These span 40.019 mm and give direction [0.990609,0.040397,-0.130621]. One is a
housing/latch surface, the other a rail, so their 5.2 mm height difference is
NOT evidence of socket tilt. This is rough housing direction, not the insertion
gap centerline or matched endpoints. It resolves the neighboring-slot ambiguity
better than independent rediscovery, without certifying the original choice.

Connector samples [312,55] and [333,109] both fail the depth-discontinuity gate.
The narrow visible contact strip cannot yet support those selected patches.
No tolerance was relaxed and no neighboring patch was silently substituted.
At 1277 only one connector point had passed, insufficient for an axis. Thus no
new arm transit, descent or release was issued in this continuation.

Three new reviews cost $0.02428375 + $0.03729625 + $0.0458775 = $0.1074575;
episode reviews now total $0.1706900, reserved-call count 4364. All private ledger
holds remain. 201 CPU tests pass, including history episode/order binding.

Current held episode d3645c724ce046aeab7dbd48580af359:1341, same worker/tunnel
as AIMED_LIFT. Selected fresh depth/calibration and images are local. Public
evidence includes connector/identity views and feature reviews at 1213,1277,1341
under `docs/evidence/aimed_lift_20260930/`. The existing video ends at 1213 and
does not include these two later camera-only moves. Full raw recordings remain
remote. No full assembly/recovery phase completed.

Next obtain a less foreshortened, better-resolved contact strip using calibrated
view geometry, or a justified edge-aware measurement with explicit uncertainty;
do not turn an RGB label into certified depth. Retain socket identity across
view changes. Do not restart the successful carry or descend on a guessed axis.
