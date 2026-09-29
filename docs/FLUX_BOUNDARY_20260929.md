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

## Native joint-position semantics

Source inspection resolves a distinction: FLUX `predict_action_chunk` returns
dataset-unit continuous predictions without a final gripper clamp, while pinned
EmbodiedSWE `vla/eval/sim.py:step_targets` explicitly applies `c.clamp(0,1)` for
`joint_pos`. Its separate `joint_target` mode intentionally preserves squeeze
intent beyond one; our adapter does NOT use that mode.

An explicit `--native-joint-pos-gripper` option now reproduces the former clamp
at our boundary, preserving raw fractions and leaving all joint targets and
execution limits unchanged. It is mutually exclusive with the earlier tolerance
option; strict zero tolerance remains the default. This is an experiment condition,
not evidence that FLUX itself produced in-range actions. No claim is made about
DROID's real actuator behavior or suitability for hardware.

`--audit-dir` saves raw NumPy predictions plus observation identity before
conversion, including rejected outputs. 118 CPU tests pass. Native semantic
compatibility does not establish task competence or contact safety.

Live proposal-only result: `runs/flux_native_probe_20260929` on observation
`3cff69ee0d184428a33eb0af51fd1937:280` passed generic action bounds and robot-only
FK preview. Three gripper entries (22,26,30) were clamped, with maximum overshoot
0.00718296. Raw arrays and identity are retained in `runs/flux_native_raw_20260929`.
No motion occurred. This particular proposal would also fit the earlier 1% mode;
it does not prove that native clamping improved task behavior. Full execution,
task transfer and contact competence remain untested.
