# Lower-view connector and socket geometry

## Current state and scope

Worker103000/8772 holds episode5fc1330e1fb9410e9cc56d5c948ee0af:1562.
No descent, insertion or release occurred in this continuation. Native grasp
assistance remains ON. Independent camera motion is idealized, without a
collision body; these results are not fixed-camera baseline results or a
real-hardware safety qualification. Control inputs remained legal RGB-D,
calibration and robot state. No new autonomous task phase is complete.

## What changed

Three observation-bound camera moves completed64actions each,192total,
12.8sim seconds and87.964summed worker wall seconds. Hand-hold errors remained
below0.83mm. The arm/gripper targets were held, not repositioned.

1.1370 to1434: lower eye [0.32,-0.14,0.33], aimed at the retained connector
   estimate. This exposed the actual gold contact strip and key, previously
   hidden behind the arm. Astra confirmed their visibility but declined exact
   bracket-side endpoint correspondence. The historical socket projected just
   below the image at approximately[319,368].
2.1434 to1498: wider eye [0.27,-0.20,0.36], aimed between the retained
   connector estimate and historical socket sample. Both features entered the
   frame. A rough inventory localized the gold strip and CPU-adjacent socket
   reinforcement rim separately; target identity was probable, not certified.
3.1498 to1562: eye [0.42,-0.06,0.32], aimed at the mean of the two CURRENT
   measured socket-rim points. This magnified the candidate socket channel.

The first two gaze targets use explicit historical/no-slip assumptions only
for camera framing, not as current contact or clearance evidence.

## Fresh measurements at1498

All four3x3 depth samples passed the unchanged10mm spread check. Their spreads
were1.62-2.16mm; these are not calibrated uncertainty bounds.

| Feature | World sample1 (m) | World sample2 (m) |
| --- | --- | --- |
| Gold connector | [0.451012,0.019462,0.170559] | [0.494277,0.019396,0.170627] |
| Socket rim | [0.455399,0.030799,0.037740] | [0.507468,0.028595,0.037758] |

The undirected sampled axes differ by2.338degrees. Minimum sampled vertical
separation is132.801mm. Sample-centroid difference is[8.789,10.268,-132.844]mm.
The longitudinal centroid difference is NOT an endpoint alignment error:
these samples were not chosen at corresponding longitudinal stations. The
socket samples lie on a rim, not a verified insertion centerline. Do not
command insertion from the centroid difference or infer full-object clearance.

## Negative results and bounded software fix

The1498 gap review could not identify two opposing rails. The closer1562 view
also returned `inspect`, noting narrow boundaries and3x3 sampling concerns.
Added an opt-in observation-only `--single-pixel-rails` prompt, restricted to
`socket_gap`, explicitly retaining mixed-pixel uncertainty and never equating
zero single-pixel spread with accuracy. The repeated1562 review still returned
`inspect`: distinguishing two opposing rails remained ambiguous. Thus the
3x3 requirement was not the sole explanation. No rail pairs were produced or
measured and no centerline was established. Do not repeat this prompt sweep.

Also allowed current, observation-ID-checked feature measurements in the gap
request so it can identify the same socket rather than implicitly switching
among parallel slots. No execution guard or completion threshold changed.
355CPU tests passed, including stale-measurement rejection and flag scoping.

## Cost, evidence and next decision

Five Astra Flex medium calls cost$0.18956875. Shared reservation count4506,
ceiling$85, existing unresolved holds preserved. No retry after an ambiguous
execution occurred. Each camera move had deterministic path preflight.

Local/remote captures: `gpu_head1434_flat`, `gpu_head1498_flat`,
`gpu_head1562_flat`; runs: `gpu_head_low_edge_view`, `gpu_head_pair_framing`,
`gpu_head_socket_closeup`. Local model outputs: `gpu_head1434_correspondence`,
`gpu_head1498_inventory`, `gpu_head1498_gap`, `gpu_head1562_gap`,
`gpu_head1562_center_ray`. Public evidence is in
`docs/evidence/low_view_geometry_20260930/`.

The outstanding decision is how to obtain/justify the mating centerline and
longitudinal correspondence for an explicitly bounded physical attempt, not
more aperture tuning or another test of whether the gold strip is visible.
Do not replace missing insertion evidence with a historical rim sample. Full
installation/release verification, autonomous recovery, and matched Direct/
Hybrid comparison remain incomplete.
