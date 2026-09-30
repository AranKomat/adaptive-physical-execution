# Independent inspection camera and integrated carry

## Scope

Simulator-only continuation toward GPU installation, not a completed task or
matched Direct/FLUX comparison. Native grasp assistance remains enabled. Camera
motion is an idealized sensor augmentation without a collision body; it is not
hardware-qualified or equivalent to the fixed-camera baseline. Only RGB-D,
calibration and robot state are used for targeting.

## Why this continuation

After the successful upward-surface regrasp, Astra confirmed retention but
could not locate the destination through the chassis wall. A second bounded
request allowed up to 20 cm of hand translation without lowering, reorientation
or opening. It returned `no_informative_motion`; no arm command followed.
The prompt now supports an explicit bounded inspection budget (default 5 cm,
maximum 20 cm), with finite-value and stage-scope validation.

The old worker on 8772 did not enable independent camera motion. Its terminal
RGB-D and journals were backed up locally in
`runs/gpu_aperture_lifted_critical_backup`; full remote recordings were retained.
Only that worker was retired. The other simulator workers were left untouched.

## Fresh episode

Episode `5fc1330e1fb9410e9cc56d5c948ee0af` on port 8772 uses the same task/seed
and initial cameras, with inspection-camera capability enabled. The grasp is
an explicitly cached/operator replay on fresh legal depth, not a fresh model
decision. The upward-face patch at [365,255] had normal/up cosine 0.99895.

- Approach: 330 actions; closure at aperture 0.3: 64 actions.
- Lift: 181 actions; final 4.573 mm error passed the declared 10 mm lift bound.
- External images showed the card held clear of its empty support at step 575.
- First camera move, 575 to 639: 64 actions, 1.021 mm hold error. The arm
  occluded most of the motherboard; the left camera still showed retention.
- A directly vertical camera destination was rejected before execution by
  the look-at singularity check. No physics step or arm retry was issued.
- Revised high-oblique camera move, 639 to 703: 64 actions, 1.018 mm hold
  error. The motherboard and candidate PCIe sockets became visible.

Camera gaze used the existing nominal workcell target [0.45,0,0.1], not a
simulator object pose. The successful camera eye was [0.50,0.02,0.95].

## Current carry selection

One Astra Flex medium call at step 703 chose `carry_above_slot`:
held connector pixel left [151,157], candidate socket right [327,202]. Cost
$0.0246275; shared reservation count 4497, approved ceiling $85.

Independent depth measurements were:

- Held feature: [0.281132,-0.362658,0.260270] m; local spread 7.259 mm.
- Socket feature: [0.475740,0.022921,0.028953] m; local spread 8.745 mm.

These are coarse surface anchors, not precise mating geometry. The plan
translates approximately 43.2 cm horizontally, preserves hand height and
aperture, and requests no insertion. Swept clearance remains unknown. The
guarded continuous carry completed at step 1023: 320 actions, 21.333 simulator
seconds, 149.747 summed worker wall seconds, 0.859 mm final position error and
0.000421 rad orientation error. All eight transit waypoints passed without
settling holds; the final stage arrived. The images still show the held card.

The history-aware correspondence review at 1023 returned `inspect`: neither
pair of mating endpoints was visible. The historical socket projections were
occluded in both external cameras and outside the wrist frame. The agent did
not substitute a neighboring slot or turn history into current clearance.
No insertion or descent followed this review. Astra then proposed camera eye
[0.82,0.15,0.62], gaze [0.468,0.007,0.4]. Local deterministic preflight rejected
its peak angular rate over 64 actions, before any simulator request. Average
direction change was not sufficient to establish the per-step angular bound.
Worker103000/8772 remains at1023; no automatic retry or reset.

The three fresh calls in this continuation cost $0.11855125 total. Shared
reservation count4499, ceiling$85, existing unresolved holds unchanged.

Removed a stale camera-prompt assertion that the current view always showed
the cooler side; the prompt now asks the model to identify current occluders.

## Evidence and next steps

Local and remote run directories: `gpu_head_enabled_approach`,
`gpu_head_enabled_close`, `gpu_head_enabled_lift`, `gpu_head_socket_view`,
`gpu_head_high_oblique_view`, `gpu_head703_flat`, and `gpu_head703_carry`.
The paid response is local `gpu_head703_carry_selection/visual_response.json`.

351 CPU tests passed. This is regression coverage, not physical task success.
Next: resolve a feasible sensor trajectory for the selected informative view,
without silently relaxing rate limits; obtain visible mating geometry while preserving the selected target,
then proceed toward alignment/insertion/release only from fresh evidence.
Autonomous installation, perturbation recovery, and matched policy comparison
remain incomplete. Do not count this camera augmentation as a baseline win.
