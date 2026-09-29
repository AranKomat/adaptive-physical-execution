# Independent inspection-camera positioning

## Scope

The opt-in `pilot_sensor_osc.py --inspection-camera` path accepts
`camera_eye_world` on a normal bounded hold phase. Only the right external
camera moves; it keeps looking at the configured generic workcell target.
This is an idealized sensor rig, not a collision-modeled camera arm. It is not
an autonomous viewpoint planner, hardware-safety demonstration, or completed
assembly phase. No simulator object pose is used to select its path.

Bounds: eye x in [0,1], y in [-0.7,0.7], z in [0.85,1.6] meters; straight-line
displacement at most 0.65 m; translation speed at most 0.12 m/s. This envelope
does not certify clearance. The requested robot target must be a hold within
3 mm / 0.03 rad of measured pose. Native control actions advance simulated
time, retain the ordinary robot stops, and consume the episode budget. Camera
readback must reach within 1 mm. Each captured RGB-D observation gets current
camera extrinsics; per-action logs include commanded eye position. Focal length
does not change. Mechanical acceleration, camera-body collision and cabling
are not modeled.

## Live results

Both tests commanded camera eye (0.45,0.5,1.4) -> (0.85,0.3,1.05), looking at
the unchanged workcell target (0.45,0,0.1), over 288 native actions / 6 seconds.
The robot held its measured reset pose, gripper open. No manipulation or model
calls were requested.

- `runs/inspection_camera_20260930`: native Fabric-backed pose route left the
  camera at its original pose and the rendered view unchanged. Endpoint error
  0.567891 m; test failed and stopped as intended. Execution wall 27.324 s.
- `runs/inspection_camera_usd_20260930`: using the pinned camera view's USD pose
  path for this sensor only passed. Endpoint error 5.46e-8 m and hand hold error
  2.98e-8 m are numerical simulator readbacks, not real-world accuracy. Execution
  wall 27.652 s; total 66.183 s including 37.006 s completed command wait.

The implementation uses the pinned IsaacLab view's private `_use_fabric` switch
and checks its presence. This compatibility point must be requalified on library
upgrades. No vendor files or robot physics settings were edited. The precise
root cause of the failed Fabric path is not isolated; do not generalize this
single test to all Fabric cameras.

The first raw result contains the historical `model_controls_targets=true` field,
which is incorrect for this operator-defined, zero-call test. That field is
removed in the corrected runner; command files carry target-source provenance.
Raw negative evidence is retained unchanged.

## Next experiment

Use this action after the already-qualified sensor-target assisted lift/carry,
where card/gripper occlusion actually occurs. Supply the fresh inspection view
along with the historical socket localization, then attempt alignment only if
the observed geometry supports it. Do not repeat a camera-only sweep or count
140 passing CPU tests as manipulation progress. Full insertion, release,
recovery and matched Direct/Hybrid comparisons remain open.
