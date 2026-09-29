# Sensor-target OSC grasp pilot

## Question

Can we retain the earlier successful OSC motor route while replacing privileged
grasp geometry with a visual model's pixel selection and measured RGB-D?
This is a bounded approach/grasp/lift qualification, NOT the full autonomous
assembly/recovery result. The operator still defines a generic phase sequence.

## Setup and separation

- Fresh seed-0 PC GPU OSC episode, same scene/robot defaults as the reference.
- Native OSC cadence 15 Hz; physics dt 1/240. The NumPy feedback port preserves
  the reference Motion gains, integral bounds, native action scales and clamps.
  It is not bit-identical Torch code and does not import payload compensation.
- Same configured left/right/wrist RGB-D cameras; live camera-pose updates.
- No object pose, object mass, hidden grasp flag or evaluator result enters the
  target selector or controller. Scoring queries happen after control ends.
- Grasp assistance remains enabled. Swept clearance is unknown and exploratory.
  This standalone pilot does not inherit the integrated IK service's guards.
  Its own limits bound the workcell, actions and final phase pose errors; they
  are not a collision certificate or a hardware execution interface.
- The original step-280 episode and FLUX service remain untouched.

Code: `pilot_sensor_osc.py`, `prepare_sensor_target_request.py`,
`plan_sensor_osc.py`, and `physical_exec.osc_reference`.

## Model contract

Two Astra Flex medium calls, JSON object responses. Each receives three current
640x360 RGB images plus robot-only state. It selects a visible top-surface pixel,
not world coordinates or object pose. The prompt distinguishes the loose card
from objects inside the chassis and allows `inspect` when the surface is unclear.
Exact prompts and responses are retained in the ignored API run directories;
the public prompt builder reproduces them from the saved captures.

The planner validates observation/calibration identity and measured depth. For
narrow top surfaces it searches at most two pixels around the selected point,
using a 3x3 footprint with at most 10 mm depth spread. This deliberately differs
from the earlier helper's default 5x5 footprint/20 mm threshold: a narrower
footprint is needed here, not a larger tolerated discontinuity. Adjustments are
recorded; continuity alone does not establish object identity or geometric center.

## Commands and observations

1. Initial Astra choice: left pixel `(163,197)`. The default 5x5 depth check
   rejected a discontinuity. The explicit bounded refinement selected `(163,196)`
   with 7.410 mm spread in its 3x3 neighborhood. Surface point:
   `(0.265772,-0.339578,0.146328)` m. Hand standoff adds 0.22 m along world z.
2. The approach ran 180 local actions with open fingers. Final hand-target error
   was 0.0903 mm, rotation error 0.0000853 rad. This is endpoint tracking error,
   not a claim of equally accurate target localization.
3. Fresh closer Astra choice: wrist pixel `(290,153)`, refined to `(290,151)`;
   3x3 depth spread 8.579 mm. Surface point:
   `(0.236518,-0.341772,0.139845)` m.
4. Grasp hand target adds the robot's documented 0.1034 m pinch-center offset
   minus a declared generic 15 mm bite below the visible surface. Top-down hand
   quaternion `(0,0,1,0)` is assumed, not a fitted object orientation.
5. Descend: 160 actions, open fingers. Close: 100 actions, **0.012 m per finger**.
   Lift: 180 actions, hand target 0.23 m higher. No hidden grasp flag authorizes
   the lift; this is a simulator-only exploratory sequence. A phase ending above
   20 mm position error or 0.15 rad rotation error aborts subsequent phases.

The 620-action total mirrors the reference's stage-1 action budget, with a fresh
visual target after approach instead of rereading hidden card pose. The broader
pilot hard cap is 700. These counts preserve reference timing for this comparison;
they are not an optimized stage controller or 620 language-model decisions.

## Cost

Approach selection: $0.02407125, 2,019 total tokens.
Closer target selection: $0.02256500, 2,012 total tokens.
Total: **two calls, $0.04663625, 4,031 tokens**. Prior unresolved reservations
remain unchanged in the private shared ledger. No policy-model inference occurs.

## First outcome: lifted, but attitude control failed

The full 620 actions executed. RGB shows the card off its stand and in the hand.
Final evaluator-only scoring confirms grasp-held=true and card z=0.257755 m;
card linear speed is approximately 4.9 mm/s. Assembly success remains false.
This is a real assisted capture/lift, but NOT a controlled, insertion-ready lift:
final hand position error was 6.719 mm while orientation error was **2.591 rad
(148.5 degrees)**, and wrist joint 7 reached 2.8973 rad. The final phase check
failed. No carry or insertion followed, and no hidden scoring was used to retry.

Descent and closure endpoint errors were 0.117/0.381 mm and 0.00361/0.00881 rad.
The trace shows rotation above 0.35 rad at descent action 197 and lift action 455;
the original pilot only checked phase endpoints and therefore failed to stop
those transients early. This is a monitoring gap, not a successful safety test.
The current runner adds a per-action 0.35 rad rotation stop and a 0.005 rad margin
to robot joint limits. It also captures the stop frame. These new guards were
NOT present in the first run; its executed source is preserved with its logs.

The initial sensor targeting no longer prevents capture altogether. But neither
the target estimator nor the loaded-arm controller is generally qualified. The
negative attitude result cannot be attributed to a single cause from this run.
Wall time was 518.167 s including paused planning/operator time, versus 41.333 s
of commanded simulation time. `inspection.mp4` shows left/wrist views at 1x
simulated time with inference/operator pauses omitted and assistance labelled.

Evidence root: `runs/sensor_osc_pilot_20260929`; model calls are separately retained
under `runs/sensor_osc_target_{approach,grasp}_20260929` and corresponding `_api`.

## Bounded ramp follow-up

Hypothesis: abrupt full-stage pose changes excite the loaded arm. A fresh
fixed-fixture episode tests a 1.5 mm/action translation ramp, the rate used in the
old reference's later carry phases, without changing OSC gains or final targets.
The stricter per-action stops above also apply; this is not a one-variable
robustness study. Cached Astra pixel choices are reused on fresh depth, explicitly
labelled template replay rather than new model decisions. No new paid calls.
Initial deprojection matches the first trial exactly; images differ slightly
from renderer noise (mean absolute channel differences below 1/255 per view).
The closer refreshed hand target differed by 0.19 mm X, 0.026 mm Y and 1.69 mm Z
from the first run, so this is not a perfectly matched fixed-coordinate ablation.

**Result:** approach, descent and closure completed; the per-action orientation
stop fired at action 489, 49 actions into the lift. Hand z rose from about 0.226 m
to 0.294 m. Final RGB shows the card lifted/tilted, and post-control scoring says
grasp-held=true, card z=0.101969 m, assembly success=false. Joint 7 was -0.114 rad,
not at its earlier 2.8973 rad limit. Physics paused at the stop; this is not a
real-hardware braking demonstration. Total wall time including planning pauses
was 253.555 s; zero new model calls.

Ramping reduced the descent's orientation disturbance, but did not establish
controlled loaded lift. Do not relax the orientation threshold or keep sweeping
ramps. Next: keep the sensor target recipe and test the native DiffIK loaded
execution route, with explicit native cadence and action-budget accounting.
The old reference's privileged payload compensation is another known difference,
not something we can silently copy into nonprivileged control.

## Retained evidence

Compact results, commands, model selections, original executed source, and the
labelled first-run inspection video are committed under
`docs/evidence/sensor_osc_pilot_20260929`. The source snapshots there are archival,
not another active runtime. The second run's results/commands are under
`docs/evidence/sensor_osc_ramp_20260929`. Full captures, action traces and logs are
backed up in their local `runs/` directories. 122 CPU tests pass, including the
new controller units/ramp/stop checks; this does not qualify the physical task.
