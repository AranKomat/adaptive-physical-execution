# Spatial grounding follow-up

The RGB-only trials do not isolate visual localization from motor tracking.
Reproduce the receipt audit with `scripts/audit_direct_tracking.py` and the
retained Direct-A, Direct-B and High run directories.

| Run | Chunk-end position error median | Maximum | Chunks over 1 cm |
|---|---:|---:|---:|
| A medium, 23 decisions | 8.59 mm | 51.87 mm | 10/23 |
| B medium, 20 decisions | 11.01 mm | 48.90 mm | 11/20 |
| A high, 20 decisions | 14.76 mm | 62.36 mm | 12/18 executed |

These are commanded-versus-measured EEF errors, not target-localization errors.
They include transient tracking; they do not prove an IK bug or establish a
grasp-specific error. Different command sequences prevent model ranking from
these numbers. No additional paid calls or robot actions were needed for this audit.

## Source findings

- `data_engine/engine/replay.py` in pinned EmbodiedSWE configures cameras with
  `data_types=["rgb"]`; current observations have no depth or calibration payload.
- The controlled/measured EEF is `panda_hand`. The prompt warns that it is not
  the contact point but supplies no numeric finger geometry.
- The robot URDF places finger link origins at local z=0.0584 m from the hand.
  This is NOT a fingertip/contact offset; finger geometry still needs inspection.
  Do not use 0.0584 m as a guessed tool-center-point correction.

## Bounded next experiment

1. Add opt-in aligned camera-plane depth and camera calibration capture, leaving
   RGB-only defaults unchanged. Preserve invalid depth and label simulator-rendered
   depth as idealized sensing, not a real depth-camera noise evaluation.
2. Verify deprojection convention and reprojection using robot geometry; use no
   simulator object transforms or segmentation IDs to choose the target.
3. Let the model identify a visible target pixel, return sensor-derived position
   with local depth spread/validity, and expose robot-only finger geometry.
   Reject mixed foreground/background neighborhoods rather than averaging them.
4. Run one bounded medium-reasoning RGB-D-assisted Direct-A episode, keeping
   scene, action limits, physics and grasp assistance unchanged. Compare contact
   approach, receipts and physical outcome against RGB-only evidence. Do not
   claim a controlled causal comparison from one stochastic episode.

Do not simultaneously alter controller timing: first inspect whether repeated
hold commands reduce endpoint error. If timing changes are needed, label that
as a separate condition. No automatic hold/retry after ambiguous execution.

## Live depth capture

Opt-in `serve_embodiedswe.py --record-depth` now records camera-plane depth,
intrinsics and optical-frame world pose alongside RGB, without changing policy
observations. The scoped camera-factory override is restored after simulator
construction; upstream source files and RGB defaults remain unchanged.

A fresh GPU worker captured seed 0 successfully, without commanded robot motion
or paid API calls. Local evidence is under `runs/depth_capture_20260929` and
`runs/depth_capture_recordings_20260929/5050474525a043cc86e8c892130f218d`.
All three depth arrays are 360x640 and have finite positive values at every pixel
in this capture. External camera focal lengths are 549.749 pixels; wrist focal
length is 320.687 pixels. These are sensor-reported intrinsics, not inferred values.
The live worker predates the extra manifest depth flags; per-frame calibration
files explicitly identify depth provenance and `policy_input=false`.

106 CPU tests pass, including a recording test for invalid-depth preservation,
alignment rejection and exclusion of arbitrary object-state metadata. This does
not qualify deprojection or prove depth accuracy. Robot-geometry reprojection,
target selection and a depth-assisted policy episode remain outstanding.

Status: receipt audit and live depth capture complete; assisted live trial not done.

## Corrected wrist calibration

The initial wrist calibration is INVALID for deprojection. Installed IsaacLab
defaults `CameraCfg.update_latest_camera_pose` to false, returning initialization
pose even for a moving link-mounted camera. Depth recording now explicitly sets
it true. This fixes calibration metadata, not the prior RGB-only policy trials:
those trials never consumed camera poses or depth.

A fresh no-motion seed-0 capture was backed up under
`runs/depth_pose_fixed_capture_20260929` and
`runs/depth_pose_fixed_recordings_20260929`. Reproduce the cross-view audit with
`scripts/audit_depth_views.py <episode-recording-directory>`.

| Source to target | Old agreement within 1 cm | Corrected agreement within 1 cm |
|---|---:|---:|
| left to right | 1009/1954 | 1009/1954 |
| left to wrist | 25/1667 | 480/539 |
| right to wrist | 4/1776 | 621/660 |
| wrist to left | 22/3207 | 1835/2857 |
| wrist to right | 6/1454 | 2692/3572 |

Denominators are positive-depth points projecting inside the destination image,
not fixed correspondences. Different poses change this overlap. The audit samples
every eighth pixel, uses nearest-pixel depths and distinguishes nearer observed
surfaces (possible occlusion) from farther surfaces. It does not mask occlusions
using simulator truth. Residual discrepancies include edges and occlusion, and
this is consistency evidence rather than metrology or collision certification.

The manually selected card surface is occluded in other views; it must not be
declared independently triangulated. Fixed-camera data is unchanged by this fix.
112 tests pass; no paid calls or commanded manipulation were used. Stage execution
and task success remain outstanding.
The overall task remains unsolved. This is a focused observation-interface test,
not a reason to restart broad perception or reasoning-level sweeps.
