# Guarded open-gripper baseline

To diagnose the native stop in the held-card episode, a fresh seed0 worker ran
the same task, controller, ramp and contact guard with the gripper open and no
object grasp. It requested a bounded 9 cm vertical move in one 64-action
chunk. The temporary worker was separate from the original simulator, FLUX,
and held-card worker, and was closed after the result.

Result: 64 actions executed, no guard stop, final position error3.793mm and
rotation error0.000321rad. The stage returned `local stage budget ended without
arrival`, because the actual tracking lag left it just outside the3mm arrival
threshold. This is not a task success or clearance certification, but it is a
useful controller baseline.

Comparison with the held-card continuation:

| condition | requested move | result | full-target position error |
| --- | ---: | --- | ---: |
| open gripper | 9 cm | 64 actions, budget ended | 3.793 mm |
| card held, gripper closed | 84 mm | guard stopped after 6 actions | 84.947 mm |

The comparison makes a generic DiffIK failure less likely. It supports a
payload/grasp-state interaction or collision/constraint near the held-card
configuration, but cannot identify which one. The guard's error is a tracking
signal, not a contact sensor. No retry or further motion was issued from the
stopped held-card worker. The next meaningful work is to improve grasp/support
observability or inspect the held-payload dynamics offline, not to loosen the
guard threshold.
