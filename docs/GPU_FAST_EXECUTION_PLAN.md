# GPU-first efficient execution and matched comparison

User direction: focus on GPU installation, not RAM. Suspend RAM experiments.
Preserve historical trials as historical evidence, not matched comparisons.

## Immediate sequence

- [ ] Free a simulator slot without losing current GPU recovery2813.
  RAM baseline726 recordings are backed up and checksum-verified; retiring a
  worker loses live physics state, not merely GPU cache. Retention decision pending.
- [ ] Qualify anti-windup on an elevated noncontact GPU-condition trajectory.
  Use the prepared bounded ramp/return probe; no repeat after ambiguous execution.
- [ ] Qualify faster transit, starting with twice the current translation and
  rotation rates. Increase further only with measured tracking and stopping
  evidence. Preserve slower approach/contact rates; do not change arrival gates.
- [ ] Demonstrate a sensor-grounded GPU grasp, lift, carry and placement with
  boundary verification. No hidden poses or collision truth in control.
- [ ] Run the matched enhanced A/B/Hybrid comparison below. Record failure and
  cost, not just success; no indefinite microdiagnostics between conditions.
- [ ] Test actual same-episode recovery and execution-memory reuse after useful
  manipulation. Installation and recovery are separate outcomes.

## Shared execution contract

Direct-A retains incremental Cartesian decisions and execution-grounded memory.
Direct-B retains absolute EEF decisions and its history semantics. Both may use
a bounded local feedback executor that interpolates and monitors motion without
asking GPT at every control latch. Larger action horizons or decision semantics
are explicitly enhanced variants, not unchanged upstream reproductions.

Local execution may interpolate an authorized target, monitor proprioception,
and stop; it must not silently choose grasp targets, invent task phases, retry,
or supply hidden scripted task solutions. Count all low-level actions and time.
Decision boundaries remain fresh observations, contact/closure, verification,
unexpected deviation, and capped stage completion, rather than arbitrary pauses.

Hybrid retains the existing accept/edit/eef/stop semantics. Accepted FLUX joint
proposals remain joint proposals with their original time/action contract.
Do NOT convert these to endpoint IK or time-compress them without separately
qualifying that transformed policy variant. Edited/FK-derived EEF proposals and
GPT EEF fallback may use the same local executor as Direct. Log their provenance
and separate their contribution from native FLUX execution.

## Matched conditions and outcomes

Freeze task initial condition/seed, camera setup, legal depth availability,
model and reasoning effort, controller version, transit/contact profiles,
arrival/stop limits, assistance flags, and overall action/time/call budgets.
Keep each mode's intended memory semantics explicit; do not add demonstrations
to only one condition. Start with one bounded trial per mode, not a broad sweep.

Report grasp, retention, placement, native isolated evaluation and recovery
separately. Also report GPT calls per meaningful stage, tokens/cost, wall time,
simulated motion time, endpoint error, peak overshoot, guards and execution-source
action counts. A controller test or visually plausible endpoint is not success.

Current status: plan adopted, execution integration and fast physical
qualification incomplete. Anti-windup is tested locally, not live-qualified.

Prepared speed profile: `elevated_open_2x`,45mm/s and0.12rad/s, versus default
22.5mm/s and0.06rad/s. Explicit request only; requires measured/commanded open
gripper, both endpoint heights>=.30m, tracking guard, and cadence<=1/15s.
Camera moves are excluded. These are experiment scope checks, NOT clearance
certification. Default/contact behavior unchanged. Worker metadata advertises
profiles; runner rejects old workers before reset. Run the ramp/return probe
with `--motion-profile elevated_open_2x` only after conservative qualification.
Not deployed or physically tested;267tests prove neither physical tracking
performance nor grasp retention. Larger rates remain deferred.
