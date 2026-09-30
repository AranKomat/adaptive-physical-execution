# RAM: next independent assembly experiment

## Live update: operator-assisted standoff reached216

New live episode `83ce804cdf06479ab757f513ab84185c:216`, worker PID78152,
remote8771/local18771. Previous observation-only episode remains closed.
FLUX is intentionally unloaded to retain this RAM scene; exact private restore
state is recorded outside artifacts at the path in the local run's
`retained_worker.json`. Do not launch FLUX alongside RAM without a memory check.
Other GPU episodes remain untouched. Do not reset the RAM episode.

Fresh Astra selected wrist[320,86], a lower ledge at z48mm rather than the
module's visible top at z68mm. That semantic selection was NOT executed or
counted as autonomous success. Previous[320,94] was a sloping/vertical side,
not merely a depth discontinuity: fitted normal is nearly horizontal. The
10mm spread gate alone cannot classify top surfaces or object identity.

Explicit operator correction selected current wrist[320,89], a visible solid
top strip. Its3x3 depth spread is0.068mm; point[.300545,-.360013,.068217]m.
The noncontact hand target is22cm world-up from that surface. Load-bearing
suitability remains unknown. No source object coordinates or evaluator were used.

New `--approach-only` mode preserves current hand attitude, requires an open
hand and tracking guard, excludes closure/descent/lift, and caps at512 actions.
This trial declared5 segments/320 maximum actions, executed38+38+38+38+64=216.
Final endpoint error2.574mm/0.000270rad,14.4 simulated seconds and93.93 execution
wall seconds. No guard stop, retry or closure. Intermediate stages did not settle;
only the final endpoint did. The module is better resolved in the final wrist
view. No grasp, installation, recovery or task phase completed.

Evidence: [wrist](evidence/ram_approach_216/04_wrist.png),
[left](evidence/ram_approach_216/04_left.png),
[receipt](evidence/ram_approach_216/04_receipt.json),
[source and operator label](evidence/ram_approach_216/source_plan.json).
Next: measure heading and contact patches from216, then bounded reorientation
and preclosure approach if justified. Do not use the GPU fixed heading.247tests
pass, including approach-only preservation/no-closure behavior; not task success.

Status: native RAM observation-only launch/capture completed. Zero commanded
control actions and zero model calls. No grasp, insertion or phase completion.

## Initial scene result

Episode `fa459b5bcfb745a2a6b9209f0839d684:0` was captured after one explicit
initial reset in a new temporary worker. Isaac initialization/warmup is not
counted as commanded control. The worker was then closed; this RAM episode is
NOT live/resumable. A physical trial needs a fresh episode and fresh targets.

- Both upright modules are visible in the left overview and wrist view. The
  wrist view crops part of the farther module; the nearer one is fully in frame.
- The right overview does not resolve DIMM insertion geometry. This is a usable
  discovery/pick starting view, not insertion readiness or certified clearance.
- Metadata confirms recorded depth, continuous transit, local DiffIK with
  rotation integral, contact tracking guard and upstream grasp-weld assistance.
- Initial launch reached readiness but capture helper was missing remotely;
  it exited without a reset request. Added prerequisite checks and synced helper.
  A subsequent preflight hit TCP TIME_WAIT, not a live worker; selected an unused
  port after checking listeners. No motion was retried.
- Idle FLUX was restored and authenticated ready as PID77661. Existing simulator
  processes were not terminated. GPU recovery was re-read afterward: still2813.
- All243 existing tests pass; the new resource probe was validated by this actual
  launch/cleanup, not by those component tests.

Evidence: [left](evidence/ram_initial_scene/000000_left.png),
[right](evidence/ram_initial_scene/000000_right.png),
[wrist](evidence/ram_initial_scene/000000_wrist.png),
[metadata](evidence/ram_initial_scene/metadata.json).
Local retained run: `runs/ram_initial_scene_capture_v2_20260930/` includes depth,
calibration, logs and restoration receipt. Script: `scripts/probe_ram_initial_scene.py`.
Next is a fresh bounded RAM grasp-selection/approach trial, not another startup
probe. Keep the same information contract below and do not reuse these targets
as current-state measurements.

## Why now

### Offline target selection follow-up

The old request builder hardcoded graphics-card identity. Added explicit
`--target-object ram_module` for approach/grasp selection only; GPU-specific
later stages reject it rather than silently issuing a wrong-object prompt.
Two regression tests added;245tests pass.

One Astra Flex medium call on the retained initial images chose the nearer
module at wrist[320,94], with long-axis samples[290,94] and[348,94]. Its grasp
claim was limited to a standoff hypothesis. Exact3x3 measured depth spreads were
10.851,9.649,10.859mm: center and second axis point FAIL the unchanged10mm gate.
No target admitted, no live action or phase completion. Raw smooth depth
variation can also trigger this gate; failure alone is not proof of mixed pixels.

Single-pixel diagnostic deprojection (NOT admitted as a motion target) shows an
approximately world-y axis at z55.3mm. Do not reuse the GPU recipe's fixed jaw
heading for this module. Neither those samples nor a nearby depth-continuous
pixel proves an upper load-bearing contact surface. Next live trial must obtain
current contact/axis evidence and derive jaw heading; do not apply cached pixels
as autonomous decisions or weaken the gate to get an approach command.

See [model selection](evidence/ram_initial_scene/target_review.json) and
[raw depth rejection](evidence/ram_initial_scene/depth_measurements.json).

The GPU episode remains at2813 with no supported contact recovery. Preserve it.
RAM is the next primary task in the original experiment sequence, not a claimed
recovery of the GPU failure. Success requires BOTH modules installed and isolated
native evaluation afterward. A first grasp/lift is an intermediate result only.

## Compatibility and evaluator-only audit

Existing `configs/tasks/pc_ram.json` passes `load_task`: registered
`assembly.pc_ram.franka.joint`, three640x360 cameras,15Hz control. The pinned
upstream registration supports the same Panda joint interface. Existing native
DiffIK, continuous intermediate waypoints and per-action tracking guards can be
used without a new controller implementation; live behavior is not yet tested.

The native robot preset starts RAM upright in holders. This is a benchmark
initialization aid, not a learned flat-object pickup result. Grasp-weld assistance
and authored invisible slot collision fixtures remain upstream defaults. This
does not solve the visual/physical-geometry mismatch found on the GPU task.
Do not feed source-derived object coordinates, slot dimensions or evaluator
tolerances into target generation. This audit is experiment selection context,
not policy input. Do not replay upstream smoke trajectories.

Sources: pinned `robobench/suites/assembly/configs/envs.py` RAM Franka registration
and `scenes/pc_ram_assembly.py` scene description. Existing task instruction stays:
"Install both loose RAM modules into the computer's DIMM slots. Verify their
placement visually." No dynamic `describe()` or extra source-derived instructions.

## Resource boundary

Measured host GPU usage:23186/24564MiB and22264/24564MiB. Do not launch a fourth
simulator into this headroom. Preserve the three existing simulator processes.
For an observation/local-control pilot, temporarily unload ONLY verified idle
FLUX, after capturing its exact command/environment securely and checking for
active requests. Restore it in cleanup and verify authenticated readiness.
Do not print tokens or retain environment secrets in experiment artifacts.
If it is busy, wait; do not kill unrelated work. A RAM-only local-control pilot
is NOT a FLUX hybrid trial. FLUX co-residency remains a separate resource issue.

## Bounded first trial

1. New isolated RAM worker and recording directory, unused loopback port;
   record legal RGB-D, enable local stages and existing rotation-integral feedback.
   Initial reset belongs only to this new episode. Keep cameras as configured;
   no geometry or grader changes. No camera sweep before examining the first view.
2. Capture initial observation, public calibration and metadata. Check image
   orientation, useful framing, measured aperture and matching observation IDs.
   If initial images cannot identify a module, stop and record the limitation.
3. One Astra Flex medium request identifies a visible module and suitable grasp
   feature using current RGB only. Depth-derived targets must come from that
   capture. Limit initial selection plus boundary review to two calls, total
   reservation cap$1, existing shared$75 ceiling and unresolved holds unchanged.
4. Qualify robot-only IK, workspace and approach from measured geometry. Do not
   reuse GPU pixel templates or call the fixed GPU recipe a RAM skill. Select
   bounded local EEF targets, continuous transit, unchanged per-action guards.
5. First physical scope ends at preclosure: open hand, at most512 control actions
   across the approach, no closure or insertion. Review fresh contact geometry
   once. Failure/ambiguous motion stops without reset, target extension or retry.
6. Only if the fresh contact evidence supports it, separately declare closure
   and short lift bounds. Verify visible retention/support clearance afterward.
   Then plan socket alignment from legal observations. A latched grasp score is
   not current retention, insertion or full task success.

## Evidence to retain

Task/config and source revision, cameras/physics assists, request/response and
cost, selected pixels and attached depth, exact action requests/receipts, first
failure and stop reason, chronological video with sim/wall timing, current
observation, and posthoc evaluator in a separate channel. Preserve negative
results. No full-phase claim until integrated native task success is verified.
