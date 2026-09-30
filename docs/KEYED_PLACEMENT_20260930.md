# Current keyed-placement review

Continuation after `81a8134` and the consolidated grasp/alignment report.
The worker was checked live by PID and a successful current `/observe`:
103000/8772, episode `5fc1330e1fb9410e9cc56d5c948ee0af:1690`.
No reset, insertion, release, hidden state query or unrelated worker change.

## Physical and sensing result

Fresh Astra review supported visible retention but declined longitudinal/key
alignment. One operator-selected oblique/top-down inspection-camera move ran
with hand hold and unchanged aperture0.3. Eye `[.48,-.18,.48]`, gaze
`[.48,.03,.09]` used the previously observed workcell region, not object truth.
The idealized camera has no collision body. This is augmented sensing, assistance
ON, operator-mediated, not an autonomous or FLUX result.

1690 ->1754:64actions,4.2667sim seconds,29.2476worker wall seconds.
Endpoint hold error0.781mm/0.001763rad; receipt `local stage arrived`.
The right image more directly exposes connector and receiving socket; card
remains visibly held. It does not resolve keyed mating placement.

## Fresh geometry and declined continuation

Astra proposed a2cm down-only noncontact approach, aperture/attitude unchanged,
and selected four solid-surface anchors. All passed current3x3 depth sampling:

| Feature | Pixel | World point (m) | Depth spread |
| --- | --- | --- | --- |
| Gold strip | right[292,156] | [.459131,.030005,.127721] |2.083mm|
| Gold strip | right[340,156] | [.494901,.029927,.127851] |2.082mm|
| Socket rim | right[290,210] | [.453366,.027939,.037650] |0.928mm|
| Socket rim | right[350,210] | [.506634,.027939,.037650] |0.928mm|

Minimum sampled vertical separation was90.071mm.
These are rough surface samples, not matching endpoints or a gap centerline.
The proposed2cm descent would leave about70.1mm sampled separation, below the
existing coarse-mode8cm floor. Existing near mode requires a corresponding end,
not merely parallel sample axes. Therefore **no descent was executed**, and no
compiler bound was relaxed or bypassed.

A current correspondence review then returned inspect, both ends null and
`key_visible=false`. It could not establish contact-strip boundaries/bracket-side
association, socket mating ends, or notch/key correspondence. This does not prove
physical impossibility; it limits the currently justified proposal.

No more nearby camera or rail-wording sweeps this continuation. Next work must
produce a task-appropriate mating-placement estimate or explicitly distinguish
a justified exploratory contact hypothesis from qualified keyed insertion.
Neither extra passing tests nor another free-space endpoint completes a phase.

## State, evidence and budget

Held worker remains at1754; no subsequent actions, contact or release.
Fresh local RGB-D/calibration: `runs/gpu_resume1754_flat_20260930`.
Remote recordings remain `runs/gpu_head_enabled_20260930/recordings`.
Selected images, request/receipt, model reviews and raw measurements:
[public evidence](evidence/keyed_placement_20260930/).

Three Astra Flex medium calls cost$0.13325125; shared reserved count4513,
ceiling$85, existing holds retained. A first launcher invocation failed on an
input path before any API reservation; the absolute-path invocation succeeded.
No API retry of an ambiguous/failed submitted request occurred. No software
changes or new tests this continuation; last recorded suite remains378CPU tests.
Installation/release, autonomous recovery and fair matched methods remain open.

## Final same-view scale diagnostic

Following external feedback, performed one focused correspondence check with
the original views plus a nearest-neighbor crop of right-image rectangle
`[180,120,410,240]`, displayed at640x334. The request supplied explicit mapping
back to original640x360 pixels; no generative enhancement or new sensor detail.
The model again returned inspect, all endpoint fields null and key not visible.
This rules out this specific presentation intervention as sufficient, not all
resolution effects or the possibility of a different estimator succeeding.

No camera/arm action, gate change or insertion attempt accompanied the check.
One Astra Flex medium call cost$0.0311275; shared count4514, ceiling$85 and
unresolved holds unchanged.
The current same-view inspection branch ends here; do not repeat crop/prompt
variants. A new attempt should explicitly change sensing or estimation condition.
The optional crop input is restricted to correspondence; four focused tests
passed for sensor-pixel preservation, coordinate metadata and invalid bounds.
This is diagnostic evidence, not physical phase completion. Selected response:
`docs/evidence/keyed_placement_20260930/closeup1754.json`.
