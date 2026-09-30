# Reviewed coarse approach and inferred-line alignment

## Current result

The same held GPU episode progressed from1562 to1690 on worker103000/8772:
`5fc1330e1fb9410e9cc56d5c948ee0af:1690`. A reviewed4cm descent and a reviewed
12.616mm horizontal correction both arrived. The final image still shows the
card held above the motherboard. No contact, insertion, release or completed
task phase is claimed. Native grasp assistance ON; augmented inspection camera;
operator-mediated compilation/review, not autonomous or FLUX Hybrid success.

## Why this differs from another rail prompt

A scene-level review confirmed that exact opposing rails are not necessary
for a coarse noncontact approach. It selected four new current surface anchors.
All four passed the existing3x3/10mm-spread depth check. They indicated about
13.2cm vertical separation. The new explicit coarse-approach mode permits only
one4cm vertical descent, preserving attitude, lateral position and aperture,
with at least8cm remaining nominal sampled separation, two qualified samples
per feature, horizontal axes within25degrees, and <=4cm transverse line offset.
These are exploratory proposal bounds, not collision clearance. Current model
approval is required; strict contact/near-standoff modes are unchanged.

Astra approved this exact proposal. Execution1562 to1626 completed64actions,
4.267sim seconds,29.547worker wall seconds; final1.704mm/0.001453rad error.
The per-action tracking guard remained enabled. No automatic retry occurred.

## A different geometric representation

At1626, the model selected three image pixels on the apparent channel CENTER,
not solid opposing rails. Each ray was intersected with a CURRENT measured
housing plane, fitted from the9-point patch at right[361,147]. That patch had
0.444mm depth spread and nearly world-up normal. These intersections are
explicitly stored as `inferred_point_world_m`, never measured gap depth or
seating depth. The calculation bounds extrapolation to15cm from the observed
plane point, rejects grazing/behind-camera rays, and requires matching
observation IDs and <=1mm plane fit RMS.

The inferred line spans approximately x0.4533..0.5122m, y0.0308..0.0299m,
z0.03754m. One gold-strip sample at right[281,155] passed the standard depth
check, yielding[0.455435,0.018130,0.127263]m. The other at[350,114] was rejected
for a depth discontinuity; it was NOT used. Single-point support does not
establish full-card angular or longitudinal alignment.

The transverse correction from that single gold point to the inferred line
was[0.000192209,0.012614944,0]m. Nominal sampled vertical separation was89.723mm.
Astra approved only that horizontal correction, preserving height, measured
attitude and aperture0.3. The existing guarded carry compiler executed one
64-action stage:1626 to1690,4.267sim seconds,29.694worker wall seconds,
0.696mm/0.001592rad final error. No descent or release accompanied it.

## Verification and limitations

378CPU tests passed. New tests cover current/historical provenance, rejection
of unsupported coarse-approach geometry, and explicit inferred-plane geometry.
The original strict modes were not relaxed. A separate neutral scene-review
builder now takes an explicit operator episode note rather than presupposing
that a contact failure happened.

Four Astra Flex medium calls cost$0.13441. Shared reservation count4510,
ceiling$85, unresolved holds retained. Total physical motion in this
continuation:128actions/8.533sim seconds/59.240summed worker wall seconds.

Current RGB-D backup: `runs/gpu_head1690_flat`. Supporting runs:
`gpu_head1562_stage_review`, `gpu_head1562_coarse_review`,
`gpu_head1562_coarse_approach`, `gpu_head1626_centerline`,
`gpu_head1626_lateral_review`, `gpu_head1626_lateral`.
Public receipts, plan and images: `docs/evidence/coarse_alignment_20260930/`.

## Next

Use fresh1690 observations to check retained grasp, current connector samples
and longitudinal/key relationship. Do not treat the previous one-point lateral
correction as full alignment, reuse stale geometry as current, or infer a gap
floor/seating depth from the housing plane. Then propose a bounded physical
continuation with an explicit abort/recovery plan. Full installation/release
verification, autonomous recovery and matched Direct/Hybrid remain unfinished.
