# Explicit FLUX gripper boundary conversion

The retained proposal in `runs/flux_capture_probe_diagnostic_20260929` had
closed-fraction predictions as low as -0.0044595003. Strict validation rejected
it. This is not evidence of task competence or a qualified action.

An optional `serve_flux.py --gripper-boundary-tolerance 0.01` now permits
saturating gripper overshoots of at most one percentage point into [0, 1].
The default remains zero tolerance. Larger overshoots, nonfinite predictions,
and malformed proposals are rejected. Joint targets are never modified.
Canonical execution validation remains unchanged.

The proposal exposes original and converted gripper fractions, changed indices,
maximum overshoot, and declared tolerance to the reviewer and trace. Hybrid
manifests also retain motor-worker metadata, including the tolerance.

On the retained proposal, indices 0, 2, 6, and 12 were saturated; all seven
joint columns were verified identical. No robot commands were issued by this
offline check. The audit is retained alongside the original raw NumPy output.

Verification: 105 CPU tests pass, including strict-default rejection, opt-in
conversion, input preservation, unchanged joints, and invalid-input rejection.
Live inference, FK/bounds qualification and Hybrid execution remain separate
requirements. Results using this conversion must not be described as raw-policy
results without the conversion disclosure.

## Live post-High probe

The restarted GPU-1 worker at `ff50bb4` loaded with tolerance 0.01. A proposal-only
request against the final Direct-A High observation returned a gripper overshoot
of 0.01310933, exceeding that tolerance. The request was rejected before an
ActionChunk or FK preview was returned. No robot motion was requested by the
probe, and full FK/bounds qualification remains incomplete. The full rejected raw
array was not retained by this server path; only its reported maximum overshoot
is available. Do not confuse it with the earlier saved raw proposal.

This demonstrates that a one-percent conversion does not generally resolve the
model's output-contract mismatch. Do not keep widening the tolerance based on
successive failures. Before Hybrid execution, inspect upstream gripper-domain
handling and preserve rejected raw predictions for a principled decision.
