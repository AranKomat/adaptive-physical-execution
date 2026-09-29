# Same-episode correction: partial contact, not a secure lift

Episode `aaddd0e351be46148b44df9a92cc8c02`, corrected bounded pose ramp from
361d702. Original cameras, FLUX gd-fp8r, Astra Flex medium. Simulator grasp
assistance remains ON and swept clearance unknown. No object truth in control.

## Results

- Hybrid executed 75 actions: 71 FLUX and four GPT EEF actions. Eight decisions,
  5 simulated seconds / 114.856 wall seconds; decision-budget termination.
  No grasp or native task success.
- Fresh sensor targeting selected wrist [333,151], without pixel refinement.
  Measured optical depth 0.101674 m, 3x3 spread 1.423 mm. The selector explicitly
  reported approximate longitudinal centering because the view clips an end.
- Operator-defined same-episode correction completed all 14 local stages:
  open/retract, five rotation segments, three standoff segments, three descent
  segments, closure and 5 cm hand lift. 896 actions / 59.733 simulated seconds /
  405.831 execution wall seconds. No model calls during these actions.
- Maximum endpoint position error was 1.596 mm. Final hand lift error was
  0.919 mm / 0.01630 rad. The bounded rotation-ramp fix therefore ran successfully
  in this episode, beyond its CPU tests.
- The card moved and tilted, but one end remained near/on the stand. A separate
  six-image before/after review returned `partial_contact`, explicitly rejecting
  a clear lift or stable suspended grasp. This agrees with direct image inspection.
- Ten paid calls total including target selection and final review: $0.97526375.

## Interpretation

This is actual object interaction after Hybrid, but NOT verified grasp-and-lift,
autonomous recovery, insertion, or completed assembly. The correction's phase
sequence, top-down attitude and bite depth were operator-defined. Endpoint
tracking accuracy does not establish good contact geometry. Simulator grasp
assistance also prevents treating any capture as a physical-hardware result.

The selected point's continuous depth does not prove longitudinal centering,
opposing-pad placement or a stable grasp. Those geometric assumptions now need
attention; another prompt-only free-running Hybrid approach does not test them.
The next grasp attempt should obtain visible opposing-contact/center evidence
and inspect geometry before closure, not merely reuse one top-surface pixel or
increase lift height. Do not carry this partially supported card as if secured.
Then expose the qualified bounded executor to model-authored recovery decisions;
the present operator sequence is not the goal's final adaptive interface.

## Outcome-blind pre-closure follow-up

One separate Astra review of observation 843 used ONLY the three pre-closure
images and robot state, without the later images, result or failure description.
It returned `inspect`: opposing pad contacts and longitudinal centering were
unconfirmed, with the right camera hiding the target and wrist contact regions
cropped/obscured. It did not establish a definite offset or obstruction. Cost
$0.02369, separate from the ten-call trial total above. This is retrospective
review evidence, not a demonstrated online prevention or successful recovery.

Added `run_grounded_correction.py --pause-before-close`, which terminates after
descent and before sending closure. A fake-client regression test checks that
all issued stages keep fingers open. This option is required for the next
grasp-geometry experiment; the existing default remains available for reproducing
the previous declared sequence. 167 CPU tests pass; no new motion in this follow-up.

Next condition: an explicitly augmented oblique inspection view of the loose
card and fingers, preserving the overview/wrist roles. Select the view from legal
observations/robot geometry, not hidden object coordinates. Pause at descent,
review opposing contact and centering, and do not proceed on `inspect`. Camera
placement is an experimental sensing change, not matched-baseline evidence or
a qualified physical camera rig. Avoid another eight-call Hybrid replay just to
test whether a new camera can see the pads.

## Retained evidence

Compact receipts, target plan, before/after images and independent visual review:
`docs/evidence/hybrid_pose_ramp_20260930`. Full local run, API audits and sensor
recordings: `runs/hybrid_pose_ramp_20260930*`. 166 CPU tests pass, which does not
complete an experiment phase. No changed camera or privileged target was used.
