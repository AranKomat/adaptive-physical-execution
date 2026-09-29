# Recovered-state continuation review

Observation1800, same held episode, no motion. One scene-level Astra Flex medium
review used only before/after withdrawal images, public robot state and the
withdrawal receipt. It did not receive evaluator scores, hidden task code or
the upstream procedure discovered in the source audit. Minimal instruction
remained unchanged. `scripts/prepare_continuation_review.py` records this input.

The first response exhausted2048output tokens and was invalid JSON (finish
reason `length`). It was rejected, not repaired or executed. A fresh request
limited output to450words/four anchors/three stages and returned valid JSON.
Costs:$0.06749625 +$0.03889 =$0.10638625; total reserved calls4372. Both settled;
prior unresolved holds remain. No further calls in this review.

The model recommends holding, measuring alignment and checking whole-assembly
interference before correction. It independently mentions possible bracket,
cooler or gripper interference, but identifies no actual collision. It does not
resolve the assembly procedure or demonstrate a successful plan in execution.

## New sensor evidence

Current right-camera pixels connector[286,91],[426,109] and
socket-rim[277,172],[407,174] all pass the existing3x3/10mm depth-spread test.
No pixel refinement or relaxed threshold. Sample separations69.148mm and76.300mm.
Undirected surface-axis difference7.947degrees; horizontal yaw difference7.924deg.
Connector sample heights101.731mm and100.995mm versus rim37.594mm.
The visual slope is thus mostly a measured heading mismatch, not large vertical
slope of these two sampled points. This does NOT recover full card orientation,
socket opening, keyed correspondence, card-to-hand rigidity or swept clearance.
The visually selected rim also need not be the exact insertion centerline.

Public response and measurement provenance:
`docs/evidence/aimed_lift_20260930/continuation_review.json` and
`docs/evidence/aimed_lift_20260930/recovered_axis_samples.json`.
RGB-D capture locally: `runs/recovered_1800_capture`.

## Next execution

Do not repeat exact-endpoint prompts. Use these measurements as an attitude
hypothesis for a bounded integrated correction on updated guard-enabled code,
with whole-card clearance explicitly unknown and a fresh visual check afterward.
No rotation/descent has been issued by this review. The running held worker has
no snapshot-export RPC; upstream state APIs alone cannot migrate it without a
new interface. Do not inject code into it or claim state restoration already
works. A separate fresh replay remains the supported route for new controller
code. Do not add a checkpoint architecture just to avoid that replay.

The instruction-assisted condition remains a separately labeled proposed
comparison, not a silent change to the current minimal-information trial.
220tests pass; no assembly phase completed by this observation-only result.
