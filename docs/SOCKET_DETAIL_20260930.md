# Higher-detail pre-grasp socket capture

Run `socket_detail_20260930`, episode `6b429bfbb76e43cebc00886aadbcb0b3`.
Separate capture-only simulator process; zero control actions, no grasp or task
completion claim. Existing simulator and FLUX services were left running.

The right camera moved from the previous initial eye (0.45,0.5,1.4) to
(0.45,0.3,0.85), with focal length 18 -> 35. Resolution remains 640x360;
the generic workcell look-at is unchanged. This changes both viewpoint and
magnification, not an isolated lens ablation. It is an idealized bodyless camera,
not collision-qualified hardware. Earlier right-camera pixel templates are invalid.

One Astra Flex medium call ($0.01924) selected center and two samples along the
upper PCIe housing rail. All three passed the unchanged 3x3 depth-continuity check
(10 mm maximum range), with measured local spread approximately 0.626 mm.
Earlier coarse-view end_a had failed that check. The new points have approximately
equal world height and define an 85.63 mm sampled span along world X. They are
interior rail samples, NOT proven physical connector endpoints or gap coordinates.

At 0.8555 m optical depth and roughly 1069 px focal length, image-plane sampling
is approximately 0.80 mm/px, versus 2.62 mm/px in the earlier overhead view.
Neither sampling scale nor local depth spread is a calibrated accuracy bound.
The renderer still reported DLSS internal resolution 371x209; magnification helped
without changing that setting, but renderer-induced error remains unmeasured.

The model still could not resolve the internal key or fully resolve the insertion
gap. A solid housing rail is useful for an axis, but should not be used as the
lateral/vertical insertion target. In particular, a changed rail-side selection
must not be interpreted as object motion or automatically converted into correction.

## Next integrated trial

Use this detailed pre-grasp view to identify the two housing rails and their gap,
and independently establish the held connector's corresponding axis/extent.
Then run the qualified lift/carry with fresh selections for the changed camera
configuration, retain these measurements as uncertain history, and revalidate
during approach. No further blind downward press is justified by this capture.
If visual asset detail cannot support the necessary correspondence, record that
limitation explicitly rather than substituting hidden fixture/seat coordinates.

Compact evidence: `docs/evidence/socket_detail_20260930`. Full initial RGB-D and
calibration are retained locally under `runs/socket_detail_20260930`.

## Stop condition reached for this view

One explicit paired-rail review returned `inspect` with no samples: the model
could not distinguish opposite rails from edges of one housing rail, and could
not establish 3x3 interior depth support. See `gap_review.json`. No inferred
gap centerline was compiled and no motion was authorized. Stop this view/prompt
branch rather than repeat it. The higher-detail housing-axis result remains valid
as a surface measurement, not a precision insertion target.

The next broader-sequence test is bounded FLUX Hybrid execution on its original
camera condition; this does not resolve or bypass the insertion-geometry issue.
