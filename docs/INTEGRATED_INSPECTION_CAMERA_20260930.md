# Integrated inspection camera: implementation, not yet live-qualified

The successful suspension episode is still paused. Its running worker has no
camera command. Editing source does not hot-reload that process.

## Contract

New launcher flag `--allow-inspection-camera` requires both
`--allow-local-stages` and `--record-depth`. Defaults remain off. `/local-stage`
accepts an optional `camera_eye_world` only under this opt-in; no unrestricted
simulator/code/state-access RPC was added.

- Only the right external camera moves. Its configured gaze target and focal
  length stay fixed; no hidden object coordinate determines either.
- Arm target must hold measured pose within 3 mm / 0.03 rad.
- Gripper command must equal the previous executed command, not the measured
  aperture (which can differ under contact). A prior command must exist.
- Camera translation is interpolated during at most 64 ordinary control actions,
  at <=0.12 m/s and <=0.65 m total displacement. Existing joint/orientation stops
  remain; camera inspection also stops for >10 mm / 0.15 rad arm-hold drift.
- Explicit integrated-camera envelope: x [0,1], y [-0.7,0.7], z [0.3,1.6] m.
  This allows departure from the existing low oblique camera. The older pilot's
  default z>=0.85 m envelope is unchanged unless explicitly selected otherwise.
- Uses the previously tested pinned IsaacLab USD camera-pose route. Fresh RGB-D
  records current camera transforms. Final camera-eye readback must be within
  1 mm, with the full action budget executed, or the worker halts without retry.
- Journals requested path, final eye error and ordinary robot receipts. RPC
  command deduplication and stale-observation checks are inherited unchanged.

This is an idealized sensor rig without collision geometry, acceleration/cabling
limits or hardware safety qualification. Its envelope is not a clearance map.
The native API/render behavior still requires live qualification in this worker.

## Validation and next run

Tests cover legacy-envelope preservation, opt-in, finite geometry, arm hold,
unchanged commanded grip, speed/displacement bounds, 64-action integrated fake
execution and ignored-camera-write failure poisoning. Tests do not establish
actual image change, held-object retention or socket visibility.
Full CPU regression: 183 passed.

Client: `scripts/probe_inspection_camera.py --url ... --observation-id ...
--eye X Y Z --output ...`. It records before/after images and requests one
64-action move, never resets or automatically retries.

Next: preserve the previous episode's evidence, then explicitly start a fresh
camera-enabled worker and reproduce the qualified suspension recipe. Reused
pixel choices must remain labeled cached templates and be deprojected on fresh
depth. The fresh process is required to install this capability, not an attempt
to pretend the old held state survived a restart. Then command a bounded camera
move while holding the card, inspect RGB/calibration/retention, and obtain a
destination feature before carry. Do not repeat an isolated empty-hand camera
sweep or claim assembly progress from the software tests alone.

## Separate motion-timing issue

The user observed stops every 3-4 seconds. The current runner allocates 64
actions (4.267 sim seconds) to each <=6 cm segment; a 5.75 cm segment ramps in
2.556 seconds at 0.0225 m/s, leaving nominal settling/holding time. No GPT call
occurs between those segments. Continuous monitored transit with settling at
meaningful contact/verification boundaries is a later improvement. Do not change
that schedule in the first camera-port qualification, which would confound it.
