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
