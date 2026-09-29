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

## Face-on measurement follow-up (predeclared)

From 1341, test eye [0.60,-0.35,0.45], gaze [0.47224,0.02803,0.20], 64 holds.
This changes the viewing direction from predominantly along the socket/card
long axis to predominantly across its observed y-normal plane. It seeks a
wider contact-strip projection without moving the card. Camera displacement
0.364 m; translational/angular preflight passed. Eye remains above case-height
features observed previously, but camera clearance is still unknown. Preserve
grip and arm target; inspect imagery before any measurement/model call.

At 1405, face-on camera move passed (0.859 mm arm error). Fresh history-aware
selection produced two valid connector samples [309,114], [355,120], depth
spreads 1.333/1.269 mm. Points [0.4630944,0.0275521,0.2608775] and
[0.5013030,0.0275279,0.2615007] give an undirected axis
[0.999867,-0.000636,0.016307], 38.214 mm separation. No measurement threshold
was changed. One current socket rail sample [357,327] passes with 9.804 mm
spread at [0.5118023,0.0253378,0.0378590]; the other is rejected.

Predeclared exploratory standoff approach: descend 0.10 m vertically in two
<=5 cm locally monitored chunks, preserve measured hand attitude and exact grip,
settle at final endpoint. Minimum current connector-surface to socket-rail
vertical separation is 0.2230 m, leaving approximately 0.1230 m. This is NOT
insertion, gap-centerline alignment, certified collision-free motion, or GPT
approval. Whole-card/bracket swept clearance is unknown; no contact intended.
Existing hard stops and strict endpoint gates remain. No release or automatic
retry. Review fresh actual images after this bounded simulator-only approach.

## Standoff approach outcome

At 1503, approach completed: 98 actions, 6.533 sim seconds, 46.310 execution
seconds, final 1.949 mm / 0.000073 rad. Card remains visibly suspended. The
12.3 cm remaining separation is a nominal feature estimate, not a calibrated
clearance bound for the whole card or bracket. No insertion or release.

Fresh correspondence review returned inspect, but now selected connector ends
right [283,209] and [382,229]. Socket ends remain unresolved. Its verbal socket
identity assessment also contradicts prior descriptions (upper/rear versus
lower/front), despite the historical image. Do not act on that inconsistency.

Geometric memory check: original legal carry socket point
[0.4722426527,0.0280299827,0.0375729090] projects through CURRENT right-camera
calibration to [320.0025,315.8249], predicted optical depth 0.5571163 m.
Current nearest-pixel depth is 0.5565141 m, difference 0.602 mm. The old anchor
has visible depth support at its projected location, but this does not prove
the original semantic choice correct or certify insertion endpoints. Next
provide this explicitly labeled projected historical anchor to correspondence
review, rather than relying only on changing verbal scene layout descriptions.
No extra camera sweep or arm move is needed for that next check.

Latest held observation d3645c724ce046aeab7dbd48580af359:1503. Camera eye
[0.60,-0.35,0.45], gaze [0.47224,0.02803,0.20]. Worker/tunnel unchanged.
Two calls $0.08973625; episode cumulative $0.26042625; reserved calls 4366.
Selected depth/calibration and receipts preserved locally; raw recordings remote.
Public face-on image, measured features, standoff image/receipt and correspondence
review added under the existing evidence directory. Video still ends at 1213.
209 tests pass. Contact-strip depth is now resolved for two rough points; matched
socket endpoints, insertion centerline/key, actual seating/release and recovery
remain open. No full assembly phase is claimed complete.
