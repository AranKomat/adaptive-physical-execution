# Fresh-target assisted regrasp and lift

## Physical Result

The failed-capture episode now has a visibly held card, clear of its support.
Live worker98214/8772: `e086f25bf69249db8d3f0a366cddf36d:1055`.
No reset, hidden object pose, latch feedback, or force reading was used.
Native grasp assistance remains ON.

Astra Flex medium selected a fresh region at right[373,260] and explicitly
chose0.3 opening after seeing the labeled aperture comparison. A measured
surface-orientation check refined the pixel to[373,258]. The open-hand descent
used84 actions and arrived; operator visual review supported closure. Closure
used64 actions and passed at1.993mm error. A pure vertical23cm target from
measured post-closure robot FK used181 actions; all intermediate waypoints
passed and the final endpoint was4.557mm short in position norm. It passed
the predeclared10mm/.03rad lift criterion. Both external images show retention
and clear separation from the support. Raw strict3mm nonarrival is preserved.

This is a successful assisted regrasp/lift, NOT full installation, FLUX Hybrid,
or fully autonomous recovery. The grasp/lift sequence and preclosure review
were operator-defined; the region and aperture came from Astra. The intervention
combined active inspection, explicit aperture experience and geometric refinement,
so it does not isolate their individual contributions.

## Concrete Geometry Fix

The prior sampler selected the nearest locally smooth depth patch within two
pixels of the requested point. At this observation, the nearest smooth patch
[372,261] is nearly vertical (absolute normal/up dot0.08879), with z0.129346m.
A nearby patch[373,258] is upward-facing (dot0.99652, roughly4.8deg tilt), with
z0.143871m. Both have excellent local planarity. Smoothness alone cannot tell a
side face from a top face; the wrong patch shifts the grasp height by about14.5mm.

`surface_patch` now measures a local9-point plane from calibrated RGB-D.
`plan_sensor_osc.py --require-upward-surface` keeps the original two-pixel search
radius but requires a plane within45deg of world up and at most1mm RMS residual.
It is explicit/opt-in for the top-down recipe, not an assertion of object
identity, opposing contact, or collision clearance. Other planner behavior is
unchanged. This is legal sensor-derived geometry, not an object-state lookup.
347 CPU tests pass, including side-versus-top and planner-selection regression.

## Efficiency And Limits

This continuation needed one new Astra call ($0.0387525). Since the failed0.0
trial ended at575, the complete experience-transfer/inspection/regrasp sequence
used four calls ($0.13304125) and480 control actions (32 simulator seconds).
Those are not full-task totals; prior aperture calibration trials are separate.
Wall time is longer than simulator time. Shared reserved-call count is4494,
ceiling$85 with existing unresolved holds retained.

The scene remains paused with the card held. Next: current feature-relative
carry and socket alignment, retaining commanded aperture0.3, with independent
retention checks. Do not repeat aperture sweeps, tiny lift tests, or attempts to
reduce the4.557mm residual merely to satisfy the old precision threshold.
Full installation, release verification and matched Direct/Hybrid comparisons
remain incomplete; no full autonomous phase is marked complete.

Public requests, receipts, images, selected plan and visual review:
`docs/evidence/upward_surface_grasp_20260930/`. Current terminal RGB-D/calibration
and command journals are backed up locally under
`runs/gpu_aperture_lifted_critical_backup`; full simulator frame history remains
remote under `runs/gpu_aperture_pair00_20260930/recordings`.
