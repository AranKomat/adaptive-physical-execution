# Retimed sensing and closer GPU standoff

Continuation of `HEAD_CAMERA_CARRY_20260930.md`. Simulator-only augmented
sensing; native grasp assistance ON. No privileged object state was used.

## Completed movement

The rejected Astra camera destination did not require a new model call or
relaxed limit. Retiming its identical linear eye/gaze path into two64-action
segments reduced peak angular speed from0.37775 to0.18902rad/s, below the
unchanged0.35rad/s bound. Both segments passed offline preflight, then arrived
at steps1087 and1151 with0.875/0.874mm hand-hold error. Total128actions,
8.533sim seconds,61.056summed worker wall seconds. This was operator retiming,
not a fresh autonomous camera plan. The final view still showed mainly the
gripper and cooler side, not sufficient mating geometry.

At1151, the source703 legal depth point was propagated using robot FK under an
explicit, unverified rigid/no-slip grasp assumption. Predicted gap to the
historical socket surface was0.22971m, with1.969mm lateral offset. A proposed
8cm descent left an estimated14.971cm gap; these are predictions, not current
object state or clearance measurements.

Astra Flex medium approved this bounded closer look ($0.0197275; shared count
4500). It explicitly did not approve insertion or certify unseen clearance.
Execution1151 to1242 completed91actions/6.067sim seconds,43.242worker wall
seconds. Intermediate transit passed without settling; final arrival error
was1.543mm/0.000127rad. Aperture0.3 and commanded attitude were preserved.
Images still show the held card; no insertion or release was attempted.

## Remaining perception issue

The external inspection view crops the lower card after descent. The next
operator-selected camera framing uses the same legal source point propagated
to current FK: [0.4750484,0.0215039,0.1770259]m. This predicted point is used
only to aim the sensor, not as fresh localization or motion-clearance evidence.
The opposite-side eye destination is [0.41,-0.14,0.60]m. Both64-action camera
segments passed unchanged path/rate preflight before the first executed.
Both arrived,1242 to1306 to1370,128actions/8.533sim seconds and57.993worker
wall seconds. Final hand-hold error0.829mm. PCB-side visibility improved, but
the arm still occludes the actual mating edge.

The independent feature inventory at1370 returned connector `occluded` and
socket `axis_visible`, with provisional target identity. The two selected
right-view housing samples [280,237] and [301,229] both passed the local depth
spread check. They span only24.679mm, with an apparent5.210mm height difference;
do not treat this short, uncertain surface axis as a verified horizontal slot
centerline or use it for insertion. Historical anchor projections are currently
depth-inconsistent. Fresh samples do not resolve the connector or target identity.

Inventory cost$0.06249; two calls this continuation total$0.0822175. Shared
reservation count4501, ceiling$85, unresolved holds retained. There was no
insertion, release, further descent, or automatic retry. Current held state:
worker103000/8772, episode5fc1330e1fb9410e9cc56d5c948ee0af:1370.

Do not repeat aperture tests or nearby high-angle camera guesses. The next
physical decision needs a view exposing the lower mating edge around the arm,
or an explicitly reviewed sensing/repositioning strategy. The current partial
socket samples are not enough to authorize contact. Strict arrival tolerances
did not block any motion in this continuation; visibility is the outstanding issue.

No new task phase is complete. Need fresh mating-feature geometry, then
alignment/insertion/release verification and the remaining autonomous recovery
and matched-method experiments. Retained observations and movements are under
`runs/gpu_head_retimed_camera_*`, `runs/gpu_head1151_standoff*`,
`runs/gpu_head1242_flat`, and `runs/gpu_head_edge_view_*`.
