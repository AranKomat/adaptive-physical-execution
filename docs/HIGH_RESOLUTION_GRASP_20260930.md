# Native-Resolution Integrated Grasp Continuation

## Condition

Separate fresh1920x1080 RGB-D episode on8780:
`28eee6eaefa546529c9118f2aff58e25`. Existing held8772 remains protected.
Fresh Astra Flex medium chooses image pixels; legal measured depth supplies
surface points. The local differential-IK sequence is operator-defined.
Native grasp assistance is ON. External clearance is unknown/exploratory.
This is neither FLUX Hybrid nor an unassisted/real-hardware result.

## Evidence So Far

At235, a new Astra target selected right[1092,765], proposing aperture0.3 from
labeled retained aperture experience. The pixel itself passed local upward
plane qualification without refinement: upward cosine0.998927, RMS2.08e-8m,
depth spread1.129mm. No object-state query supplied target geometry.

Open-hand descent completed96 actions in three continuous local stages and
paused before closure at331. Final hand error0.225mm, rotation0.000310rad.
Wall time138.85s versus6.4s simulated time. The card remains on its support;
endpoint arrival is not grasp success.

Preclosure Astra review used three bounded current overviews plus one native
right-camera crop (original box[760,650,1500,1080], explicit pixel mapping).
It returned `inspect`: partial straddling evidence, uncertain longitudinal
centering and pad/support separation. No closure was sent. A single targeted
side-on camera hold was submitted, preserving arm pose/open aperture; gaze is
the earlier legal top-surface sample, not object truth. Camera geometry is
idealized and has no physical collision body. Results must be reviewed before
any grasp command, not treated as guaranteed visibility.

The sideview hold completed64 actions at395:1.25micrometre arm tracking error,
87.42s wall time. New eye[0.30,-0.68,0.32], gaze[0.274,-0.338,0.145]. The new
right-camera crop[360,460,1480,1060] retained native detail. Astra's changed-view
review resolved reasonable longitudinal centering and found no definite bracket
contact or specific misalignment; it still returned `inspect` because opposing
pad landing areas and support separation were unresolved. No closure/lift was
issued. **Do not continue a nearby camera/prompt sweep.** Higher resolution
improved readable evidence but did not remove this occlusion. The card remains
supported and the hand open at395; original held8772 is unchanged.

Three fresh Astra calls cost$0.10610125 total; cumulative reservation count4518,
shared ceiling$85 with existing unresolved holds unchanged. This negative visual
admission result is not a failed physical grasp and not a new completed phase.

## Software Correction

Preclosure and lift review builders now reuse bounded overview encoding.
Preclosure uses native-coordinate declarations and supports explicitly mapped
sensor crops; old hardcoded640x360 language/full1920 API image payloads were
inconsistent with the new condition. No generated enhancement is used.
Tests cover640/1920 image bounds and coordinate/crop mapping; invalid crop
bounds fail before writing a request. These checks do not complete phases.
Review of a camera probe requires a matching completed open-hand hold receipt,
not an invented descent stage. Full CPU suite:398 passed.

## Next Physical Milestones

1. Before any closure, address the specific remaining contact/support ambiguity
   with sensor-derived finger/support geometry and an explicit bounded contact
   hypothesis. Stop repeating RGB-only reviews or nearby viewpoints. Neither
   the advisory model's uncertainty nor one visible free ray is a clearance
   certificate; do not relabel the existing `inspect` as approval.
2. One proposed-aperture closure and bounded short lift, with unchanged raw
   stop checks and no automatic retry. Independently compare before/after
   images for card motion, support clearance and retention.
3. If retained, continue feature-relative carry/mating using fresh native
   sensor crops. Do not reuse held8772 coordinates or infer insertion from
   hand arrival. If not retained, record the physical negative result.
4. Independently verified insertion/release and recovery remain incomplete;
   matched Direct/FLUX comparison must use equal sensing/action semantics.

Relevant local artifacts: `runs/gpu1920_close_target`,
`runs/gpu1920_open_descent_20260930`, `runs/gpu1920_preclosure_review`, and
`runs/gpu1920_preclosure_sideview_20260930`. API audits/ledger remain private.
