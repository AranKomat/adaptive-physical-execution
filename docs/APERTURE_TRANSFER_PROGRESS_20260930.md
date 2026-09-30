# Aperture experience transfer and active inspection

## What Happened

Continued the failed-capture0.0 episode, not a fresh reset:
`e086f25bf69249db8d3f0a366cddf36d`, worker98214/8772.
This is GPT-guided sensor targeting plus operator-defined local execution,
NOT FLUX Hybrid or an autonomous recovery claim.

1. At step575, Astra Flex medium received current RGB and labeled paired
   aperture evidence. It selected right[367,257] and explicitly proposed0.3
   opening. No executor override was applied. This demonstrates use of prior
   evidence, not successful transfer to a physical grasp.
2. The chosen pixel's3x3 depth footprint was discontinuous. Existing refinement
   selected[366,258], a smooth sample at world z0.12920m. A nearby current
   single-pixel sample[365,255] was z0.14401m, but its3x3 footprint was also
   discontinuous. Neither sample certifies top-face identity. No descent or
   closure was dispatched from this plan.
3. Given these raw measurements, Astra chose `inspect`, declining the target.
4. An operator-scoped wrist inspection opened the empty hand in11 actions,
   then rotated the wrist by at most0.2rad toward the coarse sensor region in
   56 actions. Both stages arrived; no hand-position translation was requested.
   The region was used for camera aiming only, not accepted as a grasp surface.
5. At step642, a new targeting call again chose0.3, with right[369,259]. The
   refined sample[368,259] had z0.12925m, again not established as the top face.
   It was used only for an open-hand inspection standoff, not closure depth.
6. The two-stage standoff used84 actions, preserved the current attitude and
   open grip, and arrived at step726 with0.691mm position error. Current wrist
   view shows a larger upper-edge region. No new grasp or installation occurred.

## Cost And Software

Three completed Astra Flex medium calls cost$0.09428875 total; shared reservation
count4493, ceiling$85, unresolved holds unchanged. A local request-preparation
error occurred before a fourth launch could submit anything: grasp-stage depth
feedback was not supported. The attempted launch failed on the missing message
file BEFORE reservation/API submission. The corrected request is included in
the three completed calls, not an extra network retry.

`prepare_sensor_target_request.py --aperture-experience` is opt-in and adds
allowlisted, provenance-checked visual trial evidence plus an explicit proposed
aperture field. It changes neither normal prompts nor model actions silently.
Current depth feedback now also supports grasp targeting and rejects stale IDs.
`run_wrist_inspection.py` supports one elevated, fixed-position, open-hand look
toward a current legal sensor region, rotation capped at0.2rad,128 actions
maximum, guards unchanged, stop without retry.341 CPU tests pass; actual
inspection stages also passed. These tests are not autonomous task completion.

## Next Step

Use the new close-range view at726 for grasp-surface localization, then perform
one integrated closure/lift if supported. Do not repeat the same far-view prompt
or conduct another aperture sweep. Continuous aperture choice is no longer the
immediate blocker; selected-face geometry is. Smooth depth does not distinguish
top from side. Consider observed local surface orientation as geometric support
if the close-range selection is still ambiguous; never infer an object pose or
clearance certificate from a single pixel.

Current images/receipts and the three model selections:
`docs/evidence/aperture_transfer_20260930/`. Full captures, aligned depth and API
audits remain under local `runs/gpu_aperture_*`; per-step simulator recordings
remain remote in `gpu_aperture_pair00_20260930/recordings`.
Other live workers, including budget-stopped Direct scene8774, were untouched.

Overall installation, autonomous recovery and matched Direct/Hybrid phases
remain incomplete. This run made an informed aperture selection and acquired a
closer view, not a successful manipulation.
