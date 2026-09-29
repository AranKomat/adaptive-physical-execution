# Close-range grasp refresh

## Predeclared protocol

Fresh episode, wrist-aim task and angular-integral worker unchanged from the
previous contact trial. Operator-defined approach uses the earlier far-view
pixel template on fresh depth ONLY for standoff. Then obtain one fresh Astra
grasp target from current camera images and measured depth before descending.
Inspect the selected surface and reject invalid depth or an inspect response.

The bounded continuation is open descent, closure, then a 23 cm vertical lift,
subdivided into at most 6 cm targets with 64 actions each. No carry or insertion
without subsequent visual evidence of suspension. Strict descent arrival remains
required; closure/lift use the already declared 10 mm / 0.15 rad exploratory
completion bounds. Hard worker abort checks remain unchanged. Stop on failure,
no automatic retry. Unknown clearance and enabled simulator grasp assistance
remain disclosed; this is not an autonomous recovery or hardware-safe plan.

This tests an integrated close-range-targeting recipe, not a clean ablation:
target refresh, lift height and action budget differ from the last trial.
No hidden object state is supplied to control or target selection.

## Outcome

Fresh episode `c3145c96f5344d6fa999b5b506de89ae` completed seven open approach
stages / 448 actions and paused at standoff. All strict arrival checks passed;
final error 1.933 mm / 0.000151 rad. This initial pause used zero paid calls.

On resumption, the live observation was unchanged. One fresh Astra selection
chose right pixel [365,256]; the bounded depth refinement used [365,255],
surface (0.274703,-0.337191,0.144790) m, optical depth 0.482572 m and 3.380 mm
local spread. This is about 20 mm laterally and 15 mm vertically from the
earlier cached point. Fresh selection considered all views; it selected the
external right view, not the wrist. Do not claim wrist-only targeting.

Two descent stages, closure and four lift stages then executed 448 actions.
Every stage passed even strict precision arrival; relaxed contact bounds were
not needed to continue. Final error: 0.817 mm / 0.002588 rad. Final observation
`c3145c96f5344d6fa999b5b506de89ae:896`. Combined approach/grasp: 896 actions,
59.733 simulated seconds, 400.042 execution wall seconds, excluding paused
review and transfer time.

The final left view shows an empty stand and suspended card. A separate
six-image before/after Astra review returned `clear_lift`, distinguishing this
from one-end tilting. It does not establish force stability, hidden clearance
or long-term retention. Target call cost $0.031565; review $0.0188025; total
$0.0503675. No privileged evaluation was supplied to either call.

This establishes a sensor-targeted assisted suspension in the integrated worker.
It remains an operator-defined sequence, not FLUX success, autonomous recovery
or full assembly. A subsequent carry-feature review is separate from this cost.

Compact evidence: `docs/evidence/close_target_20260930`; full local intermediate
stage images/receipts: `runs/close_target_20260930_{approach,grasp}`. The episode
remains paused with the card held; no release or insertion is implied.

## Carry review

One fresh current-image carry review returned `inspect`: held connector pixel
right [354,134] selected, but slot_feature=null because the motherboard socket
was occluded. No carry was issued. Cost $0.0225775; total three fresh calls
$0.072945. Next obtain a legal independent destination view while preserving
the held state, not another grasp or a carry using hidden slot coordinates.

`docs/evidence/close_target_20260930/lift_1x.mp4` uses all 897 left-camera
control-latch frames at 1x simulated time, excluding model waits and disclosing
grasp assistance. Left frames and final RGB-D are backed up locally; complete
multi-view/depth recordings remain on the host, so this is not a full disk backup.

## Inspection-action feasibility

One subsequent Astra request supplied current RGB, robot state and calibrated
sensor poses. It allowed one <=5 cm non-descending hand translation, unchanged
orientation/gripper, solely to improve observation, or no_informative_motion.
The model chose no_informative_motion: card/wrist occlusion is rigid, fixed views
remain blocked by chassis/robot, and no specific useful parallax direction was
supported. No motion was issued. This is not proof that no viewpoint exists.
Inspection planning cost $0.0266525; episode total now four calls / $0.0995975.

Source inspection confirms the integrated worker only exposes robot steps and
local stages, not the independent camera operation already tested in the older
pilot. Next port that bounded sensor-control capability; do not loop over the
same obstructed images or execute an arbitrary carry. Installing a new worker
capability requires a fresh process; do not imply a code edit changes the current
live process or silently reset its suspended episode. Preserve current evidence
before any separately declared fresh run. No task phase was completed here.
