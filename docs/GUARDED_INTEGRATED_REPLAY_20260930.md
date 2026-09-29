# Guarded integrated replay

## Protocol

Fresh worker, seed0, same wrist-aim task and minimal configured instruction.
The contact-tracking guard was loaded in a new process; the earlier held worker
and FLUX service were left untouched. The grasp/lift recipe reused the reviewed
pixel template but recomputed depth at fresh reset. No model call generated
motor targets. This remains an assisted sensor replay, not autonomous success.

The runner now has explicit `--contact-tracking-guard` support. It requires the
worker capability and attaches the guard to every local stage; absent capability
is rejected before execution.

## Result

Fresh episode `786fb059cd5440aea583ea7dabb0135d`:

- Fresh target surface: `[0.27471155, -0.33720070, 0.14479795]` m, from the
  cached pixel template `[365,256]` and current legal depth.
- Approach, closure and lift completed: 590 control actions, ending at
  observation590. Every stage returned normal arrival or continuous-transit
  receipts; no guard stop or ambiguous execution occurred.
- Endpoint errors: closure 1.211 mm / 0.00317 rad; lift 0.818 mm / 0.00302 rad.
- Posthoc native evaluator, read only after motion: `success=false`,
  `score=0.33333334`. This is the grasp rung, not insertion or seating.
- Final images support retention but do not establish a clear card/support gap.

Three bounded camera moves followed: first a gray view, then a high motherboard
view, then an opposite-side/lower view. Fresh carry reviews at observations718
and782 both returned `inspect`: the lower connector edge and separation from the
support were not visible reliably. The final view still left the relationship
ambiguous and the right view lost the card behind the case. No carry, descent,
release, or insertion command was issued.

This is useful negative evidence: endpoint accuracy and a latched grasp
milestone do not establish that the card is visually clear of its support or
ready for transport. No phase beyond the grasp milestone is complete. The next
useful change is an observable grasp/support condition or revised grasp plan
that produces a clearly visible gap, not another generic socket prompt or blind
carry. Evidence is under `runs/guarded_integrated_replay_20260930_*` and the
selected remote depth frames under `runs/guarded_integrated_replay_20260930_recordings2/`.
