# Sensor-target native DiffIK trial

## Purpose

Carry the sensor-derived grasp recipe into native DiffIK after OSC captured and
lifted the card but lost orientation. This is a contact-capable comparison, not
another free-space reach or language-model search. Goal remains nonprivileged
assembly and adaptive recovery; a stable lift alone does not finish that goal.

## Execution contract

`pilot_sensor_osc.py --controller diff_ik --ramp-targets` now selects the actual
`assembly.pc_gpu.franka.diff_ik` environment, with its native joint-PD plant and
upstream DLS controller. It does not merely run the DiffIK algorithm inside the
previous 15 Hz adapter. Absolute-target feedback computes bounded world-frame
pose error and expresses it in the native relative-delta action units; zero
delta is NOT assumed to hold an arbitrary absolute pose. There is no OSC integral
or privileged payload compensation in this route.

Native controller settings are unchanged: DLS lambda 0.05, maximum joint-command
increment 0.06 rad, command lead clamp 0.20 rad, joint-limit clamp. Outer feedback
limits error commands to 10 mm translation and 0.05 rad rotation per tick.
The 0.35 rad measured-orientation stop and 0.005 rad joint-limit margin remain.
These simulator stops pause physics; they are not hardware braking validation.

## Cadence accounting

The native leaf requests dt=0.020 s (nominal 50 Hz), but its period is rounded to
five substeps of the scene's 1/240 s physics clock. **Actual rate is 48 Hz**.
The previous OSC pilot ran at 15 Hz. The worker scales counts to preserve duration:

| Phase | OSC actions | Native DiffIK actions | Simulated seconds |
|---|---:|---:|---:|
| Standoff | 180 | 576 | 12 |
| Descent | 160 | 512 | 10.667 |
| Close | 100 | 320 | 6.667 |
| Lift | 180 | 576 | 12 |
| Total | 620 | 1,984 | 41.333 |

Translation ramp speed stays 0.0225 m/s (0.46875 mm per native tick), not
1.5 mm per native tick. Render sampling stays approximately every 2/3 simulated
second. These are differences in controller/plant/cadence, not a single-variable
ablation proving one algorithm universally superior.

The episode's explicit hard budget is 6,400 native actions (133.333 simulated
seconds), allowing separately reviewed carry commands if lift succeeds. The
first grasp/lift comparison still receives only the table's matched durations.
No automatic continuation into carry or insertion is authorized by hidden scoring.

## Target provenance

The two earlier Astra pixel choices are reused as declared fixed-fixture templates
on fresh RGB-D. Initial standoff deprojection matches the original trial exactly.
The close-view target will be remeasured after approach. This is zero new model
calls, not a claim of new autonomous discovery or robustness to layout change.
All executed commands are observation-bound. Grasp assistance remains enabled;
swept clearance remains unknown. Only post-control scoring reads object truth.

## Initial native result

All 1,984 scheduled actions ran. Hand orientation at the end of lifting was
**0.01951 rad (1.12 degrees)** from target, much better than the earlier OSC
run's 2.591 rad. But hand position remained **99.06 mm** short, so the unchanged
arrival check failed and the process ended without carry. End hand position:
`(0.269015,-0.341624,0.365126)` m. The arm was still moving; this is not evidence
of an unreachable target or a proven static stall.

Final RGB shows the card lifted. Post-control evaluator: held=true,
card z=0.168128 m, assembly success=false. Endpoint errors for approach/descent/
close were 0.346/0.760/0.645 mm and 0.000245/0.002184/0.001752 rad. Total wall
time was 303.858 s including paused planning, for 41.333 simulated seconds.
No new model calls. Evidence root: `runs/sensor_diffik_20260929`.

The old project's DiffIK comparison is not a direct reproduction target for
this grasp: `diffik_weldframe_runner.py` started from a previously successful
grasp/lift checkpoint and used privileged hand/card relative geometry. Our test
starts from the loose card and gets target geometry from RGB-D.

## Bounded follow-up, September 30 JST

The first native run used a 10 mm pose-error command cap with no integral
compensation. Upstream DiffIK relatches from the measured pose, so a held load
can require persistent nonzero error; this and the cap are plausible contributors,
not an isolated diagnosis. One follow-up adds a bounded translation integral
(0.525/s gain, +/-30 mm per axis) and a 30 mm norm cap. Rotation feedback and the
native DLS/PD settings remain unchanged. It uses no mass, COM, object pose or
hidden grasp state. This changes both integral feedback and the cap; do not
attribute an improvement to only one without an ablation.

Ordinary end-of-phase arrival failure can now pause and skip remaining phases
when explicitly requested, preserving the episode for a new observation-bound
decision. Rotation/joint-limit violations remain terminal. This fixes the pilot's
overly rigid response to a promising but incomplete movement; it does not relax
arrival tolerances or authorize an automatic retry.

Follow-up root: `runs/sensor_diffik_integral_20260930`.

## Controlled lift and carry

The integral-plus-cap follow-up passed every grasp/lift arrival check:

| Endpoint | Native action | Position error | Rotation error |
|---|---:|---:|---:|
| Standoff | 576 | 2.084 mm | 0.000166 rad |
| Descent | 1088 | 0.524 mm | 0.001974 rad |
| Close | 1408 | 2.546 mm | 0.014263 rad |
| Lift | 1984 | 1.945 mm | 0.020941 rad |
| Elevated carry midpoint | 2381 | 1.743 mm | 0.018883 rad |
| Elevated carry endpoint | 2778 | 1.661 mm | 0.017780 rad |
| 12 cm inspection retrace | 3130 | 1.688 mm | 0.018978 rad |

Images show the card above its empty support and subsequently above the chassis.
This is a controlled **assisted** lift/carry, not a completed assembly or autonomous
end-to-end plan. Initial pixel templates were reused; phase structure, offsets,
fixed attitude and inspection retrace were operator-defined.

One fresh Astra Flex medium review at action 1984 selected rough held-connector
and socket surface pixels (cost $0.0261275, 2,198 reported tokens). Legal depth
deprojection and their relative translation produced an elevated carry with
23 cm feature standoff, never lowering the hand. Two local-feedback waypoints
used 794 native actions without another model call. `plan_sensor_carry.py`
records the selections, measurements and limitations. The prior commanded
attitude, rather than its biased measured value, is preserved across phases.

At action 2778 a fresh three-view alignment review selected `inspect`: neither
the connector contact row/key nor the matching socket could be reliably located.
No descent was issued. A separately labeled operator-defined 12 cm elevated
retrace exposed a different view at action 3130. This is not an autonomous
viewpoint planner or a collision-certified path.

## Final outcome and next experiment

The second alignment review also selected `inspect`, with no feature pixels.
The card and case continued to occlude the mating geometry; no insertion or
descent was attempted. An observation-bound empty `finish=true` command ended
the episode with zero additional actions. Final evaluator, read only after
control ended: held=true, card z=0.258561 m, scene success=false.

Total: **3,130 native actions / 65.208 simulated seconds / 1,116.920 wall
seconds**, including planning, transfers and paused review. Three fresh Astra
medium Flex calls cost **$0.0686325** (carry $0.0261275, first alignment $0.0210775,
second alignment $0.0214275). Two earlier grasp-target calls were reused, not
newly executed. This accounting excludes earlier failed episodes and does not
claim an end-to-end task cost.

The full 74 MB run, including RGB-D/calibration snapshots and robot action log,
is backed up locally under the run path. Compact public evidence is in
`docs/evidence/sensor_diffik_integral_20260930`: commands, results, final scoring,
review responses, final image and a sampled two-view video. Video uses action
indices / 48 Hz for simulated timing, holds sampled frames between captures,
and excludes paused wall time. It is not a full-frame-rate recording.

Next: inspect/localize the socket before grasp/carry occludes it, using only
legal calibrated RGB-D, with visible orientation/axis evidence. Record grasped
card-to-hand geometry from observed features and robot state, then propagate
with explicit uncertainty and revalidate when visible. Do not import the
privileged replay's known socket or rigid object transforms. The alignment
prompt requires contact/key visibility; two conservative reviews are evidence
of insufficient evidence under that criterion, not proof that the simulated
asset is impossible to identify or that a new perception model is needed.

Do not repeat controller sweeps before this geometry test. Full insertion,
release, recovery, changed layouts and unassisted grasping remain untested.
130 CPU tests pass, including rejection of stale calibration, stale model
selections and inspect/stop responses in the carry compiler.
