# Hybrid to grounded correction: first integrated attempt

Episode `4ce7bec085d248b9a5f461b6a7e09807`, original cameras, FLUX gd-fp8r,
Astra Flex medium reviewer, grasp assistance enabled. Unknown clearance remains
explicit; no hidden object state entered control.

## Observed result

- Hybrid: eight decisions, 74 actions, 4.933 simulated seconds, 113.690 wall
  seconds. Ended on decision budget, not a model misalignment stop. Card remained
  on its support; native task success false.
- Fresh Astra selected left pixel [165,197] at observation 74. The existing
  bounded local refinement selected [166,196]; 3x3 depth spread 8.211 mm.
- Same-episode operator-defined correction declared 16 stages / at most 1024
  actions: open/retract, reorient, standoff, descend, close, 5 cm lift.
  This was NOT model-authored autonomous recovery.
- First 5 cm retract completed 64 actions, 4.267 simulated / 28.353 wall seconds,
  final position error 1.582 mm and rotation error 0.000391 rad.
- First rotation failed with zero confirmed actions: the bridge invoked the
  translation-only ramp, which rejects orientation changes above 0.15 rad,
  despite the bridge accepting changes up to 0.30 rad. Failure journaling caught
  this mismatch. Worker poisoned; no retry, closure, lift or task success.
- Nine total paid calls, $0.92563625, including fresh target selection. A local
  output-directory collision occurred after selection; recovered the already
  recorded response without another call. Private launcher now rejects existing
  output directories before making requests.

## Fix and next action

The local-stage bridge now uses a separate pose ramp with bounded shortest-path
world rotation at 0.06 rad/s and translation at the existing 0.0225 m/s. The old
translation-only helper remains unchanged for its existing callers. CPU regression
tests verify per-action bounds, endpoint and input rejection: 166 total tests pass.
The rotation change is NOT yet GPU-qualified.

Next: fresh integrated episode with the corrected bridge. Do not resume the
poisoned worker, repeat wording sweeps, or count this unloaded retract as a grasp.
Keep camera-motion experiments separate until this correction has meaningful
physical evidence. Autonomous recovery, insertion and full assembly remain open.

Compact evidence: `docs/evidence/hybrid_grounded_20260930`. Full local traces:
`runs/hybrid_grounded_20260930*`, including depth recordings and API audit.
