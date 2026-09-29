# Continuous-transit lift qualification

## Predeclared comparison

Fresh worker using c7deaea source changes, same wrist-aim task and angular
integral as `close_target_20260930`. The earlier episode is not reset in place;
its completed receipts, key RGB-D captures and full left video are local,
and complete multi-view/depth recordings remain on the host.

Use the same operator-defined approach/grasp/lift structure, with cached pixel
templates explicitly labeled and remeasured on fresh depth at reset and standoff.
Enable `--continuous-transit` to remove intermediate same-phase holds and retain
solver/integral state across those joins. Keep closure/final settling, speed
limits, hard stops, assistance and unknown-clearance disclosures unchanged.
No new target-selection calls are planned; review the actual final physical
effect independently. This is a fixed-fixture timing qualification, not fresh
autonomous target discovery, successful recovery or a robustness benchmark.

Inspection-camera capability is loaded but no camera command is issued until
after the lift outcome is assessed. It must not change the camera condition of
this timing comparison. No automatic retry on nonarrival or ambiguous execution.

Compare executed actions, simulated time and execution wall time to the prior
896-action / 59.733 sim-second / 400.042 execution-second run. Verify suspension
and target continuity; fewer actions alone are not success. Simulator load can
confound wall-time comparisons. No task phase is assumed complete in advance.

## Outcome

Episode `13b72700c14b45ecaca1f7e32103ae78` completed at observation 693.
Approach: 344 actions (previously 448). Grasp/lift: 349 actions (previously 448).
Combined: 693 actions / 46.200 sim seconds / 310.724 execution wall seconds,
versus 896 / 59.733 / 400.042 previously. Approximately 22.7% fewer actions
and 22.3% less execution wall time in this single comparison; not a throughput
benchmark under controlled machine load. The four lift segments used 40,39,39,64
actions rather than 64 each. Closure and final settling remain intact.

All endpoint stages passed strict arrival; pass-through waypoints met their
declared tracking bounds. Final lift error 2.351 mm / 0.000134 rad. Initial and
grasp surface points remeasured identically to the prior successful run (depth
spread differs slightly). A separate six-image review returned clear_lift:
empty cradle and elevated card, with no obvious relative slip. It cannot prove
hidden clearance or sustained stability. No new target selection or autonomous
recovery claim; cached pixels and assistance remain disclosed.

## Separate post-lift camera qualification

After the lift review, test one 64-action idealized right-camera movement from
its measured oblique start to (0.60,-0.35,0.70) m, retaining the fixed configured
gaze and focal length, measured arm pose and previous gripper command. The
translation is approximately 0.427 m over 4.267 seconds, within the declared
0.12 m/s envelope. Unknown external clearance remains explicit. Check camera
readback, fresh images/calibration and retained card before any subsequent
movement. No automatic carry, release or retry is part of this test.

Camera result: 64 actions completed at observation 757, arm error 1.021 mm /
0.002543 rad and camera-eye readback error 2.73e-8 m (simulator precision, not
real calibration accuracy). Left view still shows the card suspended. However,
the right image is almost uniformly gray and unusable for socket localization.
Finite depth covers the entire image: median 0.10449 m, range 0.07734-0.27621 m.
That supports a nearby occluding surface rather than missing depth; the exact
occluder is not identified. Do not call this successful viewpoint selection.
No carry, insertion or camera retry followed. Next choose a view that avoids
robot/fixture occlusion using legal observations and robot geometry; distinguish
camera readback success from useful sensing.

One fresh lift-review call cost $0.0194525; no new target-selection or camera
review calls. The full 1x left-view lift video excludes the later camera action:
`docs/evidence/smooth_lift_20260930/lift_1x.mp4` (694 actual control-latch frames,
model waits excluded, grasp assistance labeled). Current state is observation
`13b72700c14b45ecaca1f7e32103ae78:757`, held, paused, right view occluded.
Public receipts/images and local selected RGB-D/logs are preserved; complete
multi-view recordings remain on the host. This is not full assembly or recovery.

## Next observation action (predeclared)

From observation 757, raise only the idealized camera from (0.60,-0.35,0.70)
to (0.60,-0.35,1.15) m over 64 hold actions: 0.45 m / 4.267 seconds, below
0.12 m/s. This tests whether a substantially elevated viewpoint clears the
nearby surface seen at roughly 10 cm depth. It does not assert the exact
occluder or certify the camera path. Keep fixed gaze/focal, arm pose and prior
gripper command; inspect the image and retention before any model call or
subsequent movement. No automatic retry, carry or insertion.

Observation 821: camera raise completed, arm error 1.019 mm / 0.002540 rad.
Right view now contains the robot and motherboard instead of the gray surface;
left view still shows suspension. Lower motherboard is cropped. Next single
observation action raises the same camera to (0.60,-0.35,1.55) m over 64 holds,
0.40 m displacement, to widen coverage. Same gaze/focal/grip; no carry yet.

## Latest recorded state

Observation 885: second raise completed in 64 actions / 30.776 wall seconds,
with arm error 1.017 mm / 0.002532 rad. Eye [0.60,-0.35,1.55], fixed gaze
[0.22,-0.34,0.20]. Full motherboard is visible but small. Independent review
returned `inspect`: the card remains suspended above the empty stand, but no
reliable PCIe socket pixel was identified. No carry, insertion or release was
issued. This supersedes the observation-757 state above.

Review cost $0.031065; two current-episode reviews total $0.0505175. Evidence:
`evidence/smooth_lift_20260930/camera_high.png`, `camera_overview.png` and
`overview_review.json` in the same directory. Next obtain a closer, correctly
aimed socket view using legal observations, not privileged geometry. Raising
further would worsen resolution. Preserve the held episode; camera gaze changes
are not supported by the running worker. Complete recordings remain remote.
