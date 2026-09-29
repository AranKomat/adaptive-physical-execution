# Remove artificial inter-waypoint holds

`run_grounded_correction.py --continuous-transit` marks intermediate waypoints
within the same motion phase as pass-through. Closure, phase changes and final
lift verification retain endpoint settling. The legacy path remains available
without this flag for reproducing previous experiments.

The worker stops a pass-through chunk when its nominal ramp reaches the waypoint,
instead of spending the remaining 64-action budget holding there. It preserves
the DiffIK solver, feedback integral and nominal trajectory start across the
next observation-bound chunk. That avoids restarting the next segment from a
lagging measured pose or resetting compensation at each intermediate waypoint.
Any intervening ordinary action invalidates this continuation; changed gripper
commands or camera inspection do not reuse it.

Per-action joint/orientation guards remain active. Waypoint handoff requires
<=10 mm / 0.15 rad tracking error; failure halts without automatic retry. Each
request still has <=64 actions and the unchanged per-segment displacement and
workcell limits. Camera inspection cannot disable settling. Final arrival and
closure behavior are unchanged. This is not collision checking, continuous
force control or a certified smooth hardware trajectory.

The runner counts actual receipt actions rather than assuming 64 per chunk.
It requires the new worker capability before issuing motion. No GPT calls are
added. HTTP/image-transfer pauses remain in wall time; simulation pauses during
these waits. This removes simulated-time intermediate dwell, not all wall-clock
latency or discrete-time velocity changes at phase boundaries.

## Verification

CPU integration test: three 5.75 cm segments execute 39 + 39 + 64 actions,
versus 64 + 64 + 64 previously. It checks a single feedback-controller identity,
positive target displacement across both joins, <=1.5 mm target increments,
final settling, and a halted execution on an actuator-stall double. This is
software evidence, not a new physical speed or retention result. 184 tests pass.

For the recorded four-segment 23 cm lift, nominal timing becomes
39 + 39 + 39 + 64 = 181 actions (12.067 sim seconds), rather than 256 actions
(17.067 sim seconds): five seconds less scheduled dwell. Actual execution can
differ with initial pose and rate rounding; verify with a fresh live trace.

The current held episode runs the old loaded worker and was not reset or moved.
Next live motion qualification must use a fresh worker with this source and the
explicit runner flag. Preserve assistance/clearance disclosures and verify lift
retention before claiming a successful faster physical execution. Keep camera
movement separate from the first smoother-lift assessment.
