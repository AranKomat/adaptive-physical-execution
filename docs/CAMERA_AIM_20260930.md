# Sensor-derived inspection aiming

## Evidence and decision

The running worker was reobserved at
`13b72700c14b45ecaca1f7e32103ae78:885`; no physics action or reset was issued.
The right image shows a small motherboard below/right of the fixed gaze.
This is not evidence of successful socket identification.

Legal optical depth at right-image pixel [460,275] gives visible surface
[0.4526920775,0.0369339935,0.0321949074] m; local depth spread is 0.006337 m.
This is an operator-selected motherboard-region aiming point, NOT a selected
PCIe socket, insertion target, or privileged object pose. Three other visible
surface samples at [455,238], [483,302], [405,305] constrain approximate framing.

A coarse pinhole projection search over candidate camera eyes within 0.50 m
of the current eye, with fixed existing gaze and all samples inside a 35-pixel
image margin, found no material increase in projected region size. It ignores
occlusion, samples only part of the motherboard, and does not prove all possible
viewpoints exhausted. It supports trying adjustable aim rather than another
arbitrary translation with the same gaze.

## Implementation

Optional `camera_gaze_world` accompanies `camera_eye_world` on the existing
simulator-only local-stage endpoint. Existing opt-in, arm hold, unchanged grip,
translation limits and per-action stops still apply. Aim interpolates from the
last successful gaze, limits angular velocity to 0.35 rad/s, rejects look-at
singularities and eye/target separations below 0.1 m. Final optical-axis readback
must agree within a direction-vector error of 0.001. Failures halt the worker
without retry. Gaze paths are journaled. The client checks the new capability
before sending an aiming request to an older worker.

No camera body, cabling, collision certification or real-hardware claim.
Software tests cover successful aim, failed orientation/position readback,
speed and singularity rejection, plus existing transit and hold behavior.

## Next integrated trial

The held worker cannot load this change. Preserve its receipts and sensor data
before explicitly ending it. In a fresh worker replay the already-qualified
continuous lift with cached pixels remeasured on fresh depth; label it a
fixed-fixture replay, not autonomous rediscovery. Then aim the camera at a
freshly remeasured visible motherboard region while holding arm and grip.
Use geometric framing to choose a closer eye, subject to the same move bounds.
Review actual imagery before any carry. A motherboard-region aim must never
substitute for fresh matching connector/socket selections and depth.

Native gaze qualification, useful close socket observation, carry, insertion
and autonomous recovery remain pending. No assembly phase completed here.
