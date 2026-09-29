# GPT-6 Adaptive Physical Execution — Self-Contained Implementation & Experiment Handoff

**Date:** 2026-09-29  
**Purpose:** Handoff to an external implementation/research agent.  
**Immediate objective:** Build a compelling robotics demo quickly (hours, not weeks) that supports a broader startup thesis around reducing the cost, time, and brittleness of deploying robots into new workflows.

---

## 0. Executive summary

The current direction is **not** “GPT-6 can control a robot.” There are already many demos of that.

The desired product/demo thesis is:

> **A robot should be able to enter a new workflow, attempt the task, observe what actually happened, recover from unexpected physical states, reuse prior experience in context, and require as little task-specific robotics engineering as possible.**

The near-term experimental hypothesis is that the strongest architecture is likely:

> **a fast learned physical policy (preferably FLUX 3 Action) + GPT-6 Astra supervision/recovery + RoboICL-style interaction memory**, with a **direct GPT-6 controller (RoboICL) as the fallback/reference path** for tasks where the learned policy prior is inadequate.

The experiment should be built around a **small number of hard, visually legible technical manipulation tasks**, preferably from **EmbodiedSWE / RoboBench**, especially **GPU / RAM / PC assembly**. Use EmbodiedSWE primarily as an **environment + task + evaluator substrate**, *not* as the default coding-agent solver.

The key comparison is:

1. **Direct A — RoboICL zero-shot** (default direct controller)
2. **Direct B — GPT-as-Policy Direct** (reference direct controller)
3. **Hybrid — FLUX proposal + GPT-6 reviewer/recovery + RoboICL-style memory** (main bet)
4. **EmbodiedSWE coding-agent solution** only as fallback/control, because the user has already observed that script-based control becomes awkward when the physical state changes unexpectedly.

Do **not** spend the critical path on Unitree/UnifoLM, post-training, Qwen action-representation research, GraspGenX, or dynamic mode switching. Those are later branches.

The most valuable demo behavior is not necessarily a flawless first attempt. A stronger clip may be:

> **attempt → physical failure / slip / misalignment → observe changed state → adapt without reset, retraining, or writing a new script → succeed**

That directly communicates the deployment/ROI thesis.

---

# 1. Why this direction exists

## 1.1 The business problem

The startup direction is about making **physical automation deployable with much less engineering effort**.

Today, many robot deployments require some combination of:

- task-specific data collection,
- teleoperation,
- policy fine-tuning,
- custom perception plumbing,
- hand-written robot programs,
- manual failure handling,
- simulator engineering,
- robot-specific integration,
- repeated on-site robotics-engineer intervention.

The target buyer does not care that a robot policy benchmark is scientifically elegant. They care whether the robot:

- becomes useful quickly,
- handles variation,
- recovers when reality diverges from the nominal plan,
- reduces intervention,
- and improves ROI.

A useful framing is:

> **Give the robot a job, not a dataset.**

A stronger long-term framing is:

> **Adaptive execution / self-commissioning physical agents.**

The runtime should increasingly turn expensive frontier reasoning into cheap reusable execution.

---

## 1.2 Why the code-writing / EmbodiedSWE solver is not the primary execution model

The user has already run EmbodiedSWE-style coding-agent solutions.

A concrete failure mode occurred on a light-bulb / screw-style task:

- Codex had written code for the expected manipulation sequence.
- The bulb/object dropped into a state the script had not anticipated.
- Because the new physical state was different, the coding agent effectively needed to stop and author new logic for “pick it back up.”
- Every unexpected object displacement risks becoming a new programming problem.

This is conceptually awkward for continuous physical interaction.

The underlying problem is:

```text
task stays the same
physical state changes continuously
```

A script-centric system tends to convert new state into new code.

A visual closed-loop controller should instead do:

```text
bulb dropped
→ observe new state
→ goal is still "install bulb"
→ recover bulb
→ continue
```

without treating the changed object pose as a software-engineering event.

Coding agents remain useful for:

- synthetic-data generation,
- creating a first solution when nothing else works,
- simulator construction,
- generating reusable classical controllers,
- compilation/distillation,
- fallback commissioning.

But they should not be the normal online physical-control abstraction.

---

# 2. Adjacent systems and how to use them

## 2.1 RoboICL — default direct GPT controller template

**Primary links**

- Paper: https://arxiv.org/abs/2609.34261
- Project page: https://mosi-ai.github.io/RoboICL-GPT6-Astra.github.io/
- GitHub: https://github.com/Mosi-AI/RoboICL

RoboICL is highly relevant because it explicitly treats a frozen multimodal frontier model as a robot policy **without parameter updates**.

Its key ideas:

- GPT-6 Astra is the sole learned action generator.
- The model directly outputs bounded dual-arm Cartesian actions.
- Demonstrations and live deployment history use the same interaction grammar:

```text
observation
→ action
→ execution feedback / receipt
→ next observation
```

- It has **bounded anchored LIVE memory**, preserving selected full-resolution historical interactions while explicitly marking omitted spans.
- It withholds privileged evaluator information such as reward, success score, hidden object pose, task code, and layout metadata from action generation.
- The current public description uses a constrained `Act` interface with low-level Cartesian action sequences.

This is the **default Direct-A implementation** to port.

### Important distinction: two kinds of ICL

RoboICL mixes two forms of useful context:

1. **Interaction memory** — what this robot just tried and what physically happened.
2. **Demonstration context** — reference trajectories from previous successful episodes.

For our purposes, interaction memory is probably more universally useful.

Demonstrations can help, but can also overconstrain behavior to a particular geometry or motion. A key future idea is to separate:

- **procedural ICL**: “grasp → align → insert → verify”
- **motor ICL**: exact motion deltas from a prior geometry

The first should generalize better across layout / sim-to-real changes.

### Why RoboICL is useful for the demo

It naturally enables the desired story:

```text
attempt
→ observe result
→ remember action + result
→ alter next action
→ recover
```

No retraining is required.

---

## 2.2 GPT-as-Policy — hybrid runtime skeleton + Direct-B reference

**Primary links**

- Public report: https://anonymous-report-421.github.io/public-website/?lang=en&view=1
- GitHub: https://github.com/anonymous-report-421/GPT-as-Policy

This project contains two very important modes:

### Direct

GPT-6 directly authors bounded end-effector actions.

Use this as **Direct-B**, a comparison/reference implementation.

### Hybrid

A learned robot policy proposes a physical action segment; GPT-6 reviews it and can accept, shorten, edit, or replace it.

Conceptually:

```text
observation
→ π0.5 proposal
→ GPT-6 review/correction
→ execute
→ new observation
→ repeat
```

The released implementation keeps a **persistent Codex/GPT thread** through the episode and records actual execution history, so the agent can reason about prior actions and mistakes.

This is the best existing skeleton for the **hybrid branch**.

### Published resource/usage numbers worth understanding

From the report’s 50 selected run instances per architecture:

| Metric | π0.5 + GPT-6 hybrid | GPT-6 Direct |
|---|---:|---:|
| Executed control steps | 42,750 | 38,221 |
| Executed action segments | 3,776 | 7,729 |
| Mean physical duration, excluding model latency | 34.20 s | 30.58 s |
| Total tokens incl. cached input | 624,762,828 | 1,132,343,772 |
| Uncached input tokens | 15,901,963 | 22,907,448 |
| Output tokens | 1,305,025 | 2,086,564 |
| Reported success on selected task panel | 48% | 26% |

This is roughly:

- **75.5 action segments / decisions per episode** for hybrid
- **154.6 per episode** for Direct
- ~**12.5M total tokens/episode** for hybrid
- ~**22.6M total tokens/episode** for Direct

The hybrid report also says:

- 85.6% of executed control steps followed the student policy
- 14.4% of executed steps were GPT-corrected

**Critical interpretation:** the 14.4% correction rate does **not** mean GPT is invoked only 14.4% of the time. GPT still reviews candidate segments at decision points. Therefore the current hybrid is more efficient than Direct but is still not the final latency-efficient production architecture.

### Reasoning setting

The public GPT-as-Policy repository pins:

```text
model = gpt-6-astra
reasoning effort = xhigh
```

for its published hybrid/direct runtime.

This likely contributes significantly to latency.

---

## 2.3 FLUX 3 Action — preferred learned physical prior for hybrid

**Primary links**

- Product/model page: https://bfl.ai/models/flux-3-action
- GitHub: https://github.com/black-forest-labs/flux-action
- Hugging Face collection: https://huggingface.co/collections/black-forest-labs/flux-3-action
- DROID checkpoint: https://huggingface.co/black-forest-labs/flux-3-action-droid

FLUX should be treated as a **general learned visuomotor prior**, not as the intelligence layer.

Why it is attractive:

- recently released,
- DROID policy checkpoint available,
- official inference code,
- supports action prediction rather than only grasp generation,
- closer to general manipulation than narrow primitives such as GraspGenX.

For the current experiment, FLUX should replace / supplement the π0.5 proposal source in the GPT-as-Policy hybrid.

### Important embodiment choice

EmbodiedSWE has multiple robot embodiments, including Franka.

DROID is naturally associated with a Franka-style manipulation setup, so **choose a Franka EmbodiedSWE task configuration wherever possible** to minimize embodiment/action-adapter mismatch.

Do not spend time proving broad cross-embodiment transfer tonight.

---

## 2.4 EmbodiedSWE — task/environment/evaluator, not default solver

**Primary links**

- Project: https://embodiedswe.github.io/
- GitHub: https://github.com/EmbodiedSWE/EmbodiedSWE
- Paper: https://arxiv.org/abs/2609.27308

EmbodiedSWE contains hard technical manipulation tasks and infrastructure built on Isaac Lab / RoboBench.

Relevant repo capabilities include:

- task environments,
- multiple robot embodiments,
- controllers,
- graders/evaluators,
- video recording,
- coding-agent evaluation,
- data generation,
- real-to-sim utilities.

The official EmbodiedSWE solver framing is based on a coding agent writing a Python `solve(env)` procedure.

**We should not use that as the main policy.**

Use:

```text
EmbodiedSWE
= world + assets + task definition + robot + evaluator + recording
```

while replacing:

```text
coding agent writes robot program
```

with:

```text
Direct RoboICL
or
FLUX + GPT hybrid
```

### Important fairness / real-world relevance constraint

The standard coding-agent setting may allow scene-inspection and simulator information that is appropriate for synthetic-data generation but less representative of real deployment.

For our experiment, make a **non-privileged observation adapter**.

Prefer exposing only:

- RGB camera(s)
- wrist camera(s) if available
- RGB-D only if it corresponds to a realistic sensor
- proprioception
- EEF pose
- gripper state
- task instruction
- previous execution receipts / controller feedback

Do **not** expose to GPT:

- ground-truth object positions,
- scene graph internals,
- hidden simulator state,
- grader state,
- reward,
- success labels,
- exact task code,
- privileged geometry,
- environment internals that would not exist in a real deployment.

The point is to test whether the controller can recover from the *observed physical state*.

---

## 2.5 General Deployment — adjacent company to differentiate from

- https://generaldeployments.com/

General Deployment publicly frames itself around:

```text
capture customer site
→ reconstruct digital twin
→ run policy under condition sweeps
→ produce ranked failure map
```

This is adjacent and useful, but we should **not** make “better real2sim + eval” the center of our story.

Our center of gravity should be:

```text
new physical workflow
→ execute
→ observe what actually happened
→ adapt
→ recover
→ remember
→ reduce future intervention
```

A concise distinction:

> **General Deployment asks: “Where does this policy fail in this deployment?”**  
> **Our direction asks: “How do we make the robot start working here with as little deployment engineering as possible, and recover when reality differs from the nominal plan?”**

Digital twins can be an input to our system; they do not need to be our primary moat.

---

## 2.6 Secondary / later sources

### RoboProbe / RoboDojo GPT-6 evaluation

- GPT-6 evaluation report: https://robodojo-benchmark.com/report/gpt-6-astra-eval
- RoboProbe GitHub: https://github.com/RoboProbe/RoboProbe
- Related paper supplied previously: https://arxiv.org/pdf/2609.24170

Useful for understanding where direct frontier-model control succeeds/fails and for fallback tasks.

### Qwen action-representation alignment — later, not tonight

- https://arxiv.org/pdf/2606.17846

Potential future experiment: make GPT’s action representation more visually aligned (e.g. camera-aligned relative actions) rather than world-frame Cartesian deltas.

Do **not** put this in the current critical path.

### GraspGenX — specialist grasp/regrasp tool, not core policy

- Project: https://graspgenx.github.io/
- GitHub: https://github.com/NVlabs/GraspGenX

Useful later as a specialist for robust grasp pose generation. Too narrow to solve contact-rich tasks such as screwing, insertion, folding, or general manipulation. Do not make it the hero architecture.

---

# 3. Current architecture decision

## 3.1 Direct-A — RoboICL zero-shot (default direct controller)

Goal: reproduce / port RoboICL as faithfully as practical.

Conceptual loop:

```text
task
+
current observation
+
proprio
+
bounded LIVE interaction memory
+
(optional reference demonstrations)
        ↓
GPT-6 Astra
        ↓
bounded Cartesian action sequence
        ↓
deterministic validation / IK / execution
        ↓
execution receipt + new observation
        ↺
```

**Start zero-shot.**

Do not depend on task-specific reference demonstrations for the first EmbodiedSWE port.

If a previously successful rollout exists, later try it as reference context.

### Why Direct-A exists

Some tasks may be too far outside the learned FLUX prior.

Direct GPT is inefficient, but it is potentially the most general fallback.

The goal is **not** to prove direct GPT is fast enough for production.

The goal is to determine whether it can handle strange states/tasks without new code or training.

---

## 3.2 Direct-B — GPT-as-Policy Direct

Run / port the public Direct mode with minimal changes.

Purpose:

- reference comparison to RoboICL direct,
- test whether RoboICL’s action/memory design is actually the improvement,
- retain a second direct-control implementation without inventing a new one.

Do not heavily customize it before getting a baseline.

---

## 3.3 Hybrid — main bet

The preferred architecture:

```text
current observation
+ task
+ execution memory
       │
       ├────────────→ FLUX proposes action chunk
       │
       ▼
     GPT-6
       │
       ├─ accept
       ├─ execute shorter prefix
       ├─ edit
       └─ override / direct correction
       ↓
     execute
       ↓
new observation + actual result
       ↓
RoboICL-style memory
       ↺
```

Implementation philosophy:

> **Start from the GPT-as-Policy hybrid runtime rather than inventing a new gate. Replace the student policy proposal source with FLUX, then progressively borrow the useful memory design from RoboICL.**

This is the most promising path because it combines:

- fast learned motor behavior,
- frontier semantic/spatial reasoning,
- recovery,
- stateful context,
- no task-specific weight update.

---

# 4. Do not implement dynamic mode switching yet

Longer-term we probably want:

```text
FLUX default
→ repeated failure / OOD / low confidence
→ GPT Direct
→ recover
→ hand back
```

But **do not make this part of tonight’s critical path**.

Reasons:

- defines a new failure detector,
- creates ambiguity about when to switch,
- complicates context transfer,
- adds confounds,
- makes debugging harder,
- tasks are not necessarily long enough to justify mode switching.

For the first experiment, choose the controller mode **before the episode**.

Run the same task under:

```text
A. RoboICL Direct
B. GPT-as-Policy Direct
C. FLUX + GPT Hybrid + memory
```

Later add switching once the components are proven.

---

# 5. Reasoning-effort policy

## 5.1 Published setups are expensive

GPT-as-Policy uses GPT-6 Astra at **xhigh**.

RoboICL’s published control experiments also use high reasoning settings in its reported setup, and direct control is very slow because there are many calls per episode.

The user has personally found **Medium** sufficient for difficult robotics reasoning / EmbodiedSWE coding experiments and believes GPT-6 is relatively token-efficient.

## 5.2 Experiment strategy

For our demo:

### Start with Medium

Use:

```text
gpt-6-astra
reasoning = medium
```

for initial hybrid and direct smoke tests.

Why:

- we are not reproducing a paper benchmark,
- we care about successful demo latency,
- hybrid supervision should be easier than generating every low-level action directly,
- xhigh may be unnecessary on easy/repetitive decisions.

### Escalate only when useful

If Medium:

- understands the task,
- understands the scene,
- but makes repeatedly poor physical decisions,

try High / XHigh.

If the task is nearly solved at Medium, do not automatically pay for XHigh.

### Record reasoning effort in every artifact

Every run must save:

```text
model
reasoning_effort
number_of_model_calls
token_usage
provider/API latency
wall-clock episode time
```

This is part of the actual deployment economics.

---

# 6. Task selection

Do not solve a broad benchmark tonight.

Focus on **2–3 technical tasks**.

## Primary candidates

### 1. PC GPU installation / insertion

Best first task.

Why:

- visually legible,
- technical / industrial-looking,
- precision required,
- less toy-like than blocks,
- relevant to real automation,
- the user already has EmbodiedSWE experience.

### 2. RAM installation

Good because:

- precision/contact rich,
- simple goal,
- visually understandable,
- complementary to GPU insertion.

### 3. GPU + RAM multi-stage task

Use only after individual tasks are working.

This is the strongest hero clip if successful.

## Secondary recovery-specific candidate

### Bulb / screw task

The user has already observed the coding-agent failure mode here.

This is attractive specifically if it produces:

```text
bulb slips / drops
→ robot sees new state
→ no reset
→ no new script
→ direct/hybrid controller recovers
→ resumes task
```

This may be the best **qualitative recovery demo**, even if GPU/RAM is the cleaner business visual.

---

# 7. Fallback task environments

If EmbodiedSWE integration takes too long:

## RoboDojo fallback

Potentially useful tasks:

- `fasten_screws`
- `plug_in_charger`
- `insert_key`
- `insert_tubes`
- `fold_clothes`
- `store_tools_in_toolbox`
- `imitate_sorting_sequence`
- conveyor tasks

RoboDojo is not the ideal hero visual, but it is a reliable control-harness test surface.

## RoboCasa fallback

RoboCasa is visually richer and can support household / kitchen workflows, but it is less directly aligned with the current industrial/technical ROI narrative.

Use only if needed.

---

# 8. What a successful demo should show

The demo does **not** need high benchmark accuracy.

A single successful rollout can be sufficient for a founder/investor demo if represented honestly.

The highest-value qualitative behavior is:

```text
1. robot attempts hard task
2. physical state diverges from plan
3. controller observes changed state
4. context remembers what happened
5. controller changes action/strategy
6. no reset / no retraining / no new code
7. task succeeds
```

Potential on-screen labels:

```text
Attempt 1
→ alignment failed

Execution memory updated

GPT-6:
"Connector is misaligned; re-approach from current pose."

FLUX proposal / direct correction

Attempt 2
→ seated successfully
```

Best high-level message:

> **No reset. No new code. No task-specific training.**

If the recording is sped up, **label the playback speed**. Do not imply real-time execution if it was accelerated.

---

# 9. The memory design

## 9.1 Baseline: preserve RoboICL semantics

For the first implementation, keep the interaction unit close to:

```text
OBSERVATION
- camera views
- proprio

ACTION
- action chunk proposed

RECEIPT
- actual executed prefix
- interruption / validation / controller feedback

RESULTING OBSERVATION
- camera views
- proprio
```

This is important: the memory should represent **what actually happened**, not only what GPT intended.

---

## 9.2 Suggested runtime memory record

Internally it can be stored as something like:

```yaml
step_id: 7
subgoal: "align GPU connector with PCIe slot"
observation:
  rgb_refs: [...]
  proprio_ref: ...
executor: "flux_hybrid"
proposal_ref: ...
executed_prefix: ...
receipt:
  interruption: null
  controller_status: ok
after_observation:
  rgb_refs: [...]
  proprio_ref: ...
```

Do not invent semantic labels such as “object slipped” from simulator truth. If a semantic summary is generated, make it explicitly model-derived from observable evidence.

---

## 9.3 Future idea: compact context compiler

The user suspects ICL may improve if historical information is compressed into a compact, highly usable representation.

This is plausible and worth a later experiment.

Current RoboICL retains selected raw/full-resolution chunks and explicit gaps.

A future memory compiler might maintain:

```text
CURRENT GOAL
Install GPU.

CONFIRMED PROGRESS
GPU removed from packaging.
Slot visually located.

LAST FAILURE
Insertion approached too high; connector did not seat.

CURRENT STATE
GPU still grasped; rotated clockwise ~small amount.

REUSABLE LESSON
Approach lower and align connector edge before forward insertion.

KEY VISUALS
[before image] [after image]
```

while still retaining raw interaction references.

Potential benefits:

- fewer tokens,
- easier retrieval,
- less irrelevant historical geometry,
- stronger procedural generalization,
- less overfitting to exact demonstration trajectories.

**Do not make this a prerequisite for the first baseline.**

First establish that the original memory/control loops work in the new environment.

---

# 10. Observation / action contract for EmbodiedSWE adapter

Create a small stable adapter layer so Direct and Hybrid share the same physical environment.

Suggested conceptual contract:

```python
Observation:
    task_instruction
    head_rgb / main_rgb
    wrist_rgb_left? / wrist_rgb_right?
    depth?                 # only if realistic sensor path
    joint_state
    eef_pose
    gripper_state
    remaining_time?        # avoid if not realistic / evaluator-derived
```

Avoid passing:

```python
object_ground_truth_pose
task_reward
success_flag
grader_progress
scene_graph
exact target coordinates
hidden collision data
task source code
```

Suggested action paths:

```text
Direct:
GPT Cartesian deltas / targets
→ deterministic bounds
→ IK/controller
→ sim

Hybrid:
FLUX action chunk
→ GPT review/edit
→ deterministic bounds
→ controller
→ sim
```

The simulator’s official evaluator can still assess success **outside the policy context**.

---

# 11. Implementation sequence

## Phase 0 — Freeze scope

Critical path contains only:

- EmbodiedSWE environment/evaluator
- RoboICL Direct
- GPT-as-Policy Direct
- GPT-as-Policy Hybrid skeleton
- FLUX proposal source
- execution-memory plumbing
- recording/logging

Explicitly defer:

- Unitree / UnifoLM
- post-training
- τ₀ integration
- GraspGenX
- Qwen action representation
- new world-model training
- automatic controller switching
- broad benchmark evaluation
- extensive sim2real work

---

## Phase 1 — Validate all upstream components unchanged

Before porting:

### RoboICL

Run:

- dry-run / preflight
- capture-only
- one zero-shot RoboDojo rollout

Goal: verify exact upstream behavior and file formats.

### GPT-as-Policy

Run one original:

- Direct rollout
- hybrid rollout

Goal: understand:

- persistent thread,
- tool calls,
- action proposal format,
- history storage,
- execution receipts,
- video output.

### FLUX

Run official DROID inference path and inspect:

- expected observations,
- image conventions,
- robot state/action dimensions,
- action horizon,
- output format,
- normalization.

Do not begin environment integration before each component works in its native configuration.

---

## Phase 2 — Build EmbodiedSWE policy adapter

Pick **Franka** embodiment first.

Target tasks:

1. GPU
2. RAM
3. GPU+RAM only after 1/2

Build:

```text
EmbodiedSWE env
      ↓
policy-safe observation extraction
      ↓
generic policy server/client boundary
      ↓
bounded action executor
      ↓
native EmbodiedSWE grader
```

Requirements:

- no privileged state to GPT,
- save every observation,
- save every executed action,
- record timestamps,
- record task/eval result separately from policy context,
- video rendering.

First test with trivial deterministic actions / manual actions.

---

## Phase 3 — Port Direct-A: RoboICL zero-shot

Preserve as much upstream behavior as possible.

Do **not** “improve” the prompt/action representation immediately.

Keep:

- execution-grounded grammar,
- bounded memory,
- same type of Cartesian action interface,
- deterministic validation,
- per-turn re-observation.

Adapt only:

- camera mapping,
- robot state mapping,
- controller / IK interface,
- task name/instruction,
- horizon if required by control frequency.

Start Medium.

Run one GPU episode.

If near-success, try multiple seeds / modest reasoning escalation.

---

## Phase 4 — Port Direct-B: GPT-as-Policy Direct

Use the public direct controller as the second direct baseline.

Preserve:

- persistent thread,
- bounded EEF interface,
- actual execution history,
- same-episode context.

Again, only adapt environment/control interface.

Start Medium.

The goal is not broad evaluation. It is comparison with RoboICL on the same task.

---

## Phase 5 — Hybrid with existing student first

Before FLUX if necessary, make the GPT-as-Policy hybrid semantics work in EmbodiedSWE with the easiest compatible proposal source.

The objective is to validate:

```text
proposal
→ GPT review
→ execution
→ receipt
→ persistent context
```

Once this works, substitute FLUX.

If using π0.5 temporarily is significantly easier, it is acceptable as a plumbing test.

---

## Phase 6 — Substitute FLUX

Prefer the DROID checkpoint.

Select the Franka environment/action contract to minimize embodiment mismatch.

Implement the thinnest possible adapter:

```text
EmbodiedSWE observation
→ FLUX observation schema
→ FLUX action chunk
→ physical proposal representation
→ GPT-as-Policy reviewer
→ controller
```

Do not retrain FLUX tonight.

If the output action semantics do not align cleanly, stop before spending hours on invasive transformation.

---

## Phase 7 — Add RoboICL-style memory to hybrid

Once hybrid is functioning, improve context with:

- observation → action → receipt → observation records,
- selected historical anchors,
- explicit omitted spans if truncating,
- previous actual execution result,
- latest/current observation.

Do not feed simulator reward/success/object truth.

This is the architecture expected to be most promising.

---

# 12. Experiment matrix

Keep it small.

For each primary task:

| Run | Controller | Reasoning | Demonstrations | Goal |
|---|---|---|---|---|
| A | RoboICL Direct | Medium | 0-shot | general direct controller |
| B | GPT-as-Policy Direct | Medium | none | direct reference |
| C | FLUX + GPT Hybrid + memory | Medium | none | main architecture |
| D | strongest near-miss | High/XHigh | same | rescue promising run |
| E | optional | Medium | 1 prior successful trace | test ICL reuse |

Do not run E until one system has a successful trace.

---

# 13. Evaluation criteria

For the immediate demo, **success once matters more than benchmark average**.

But every run should record enough data to avoid fooling ourselves.

## Must record

- task
- environment config
- robot embodiment
- seed/layout
- controller mode
- model name/version
- reasoning effort
- total GPT calls
- provider/API latency per call
- wall-clock episode time
- simulated physical time
- total tokens
- cached vs uncached input if available
- output tokens
- proposal count
- GPT overrides/edits
- executed steps by source
- terminal evaluator result
- partial score if available
- whether privileged simulator information entered policy context
- all videos
- all observations/actions/receipts

## Qualitative tags

Manually annotate:

- unexpected state occurred?
- object slipped/dropped?
- misalignment?
- controller noticed?
- changed strategy?
- recovered?
- repeated same mistake?
- needed reset?
- needed code modification?
- demonstrated genuine memory use?

A run with a clean recovery can be more valuable than a trivial first-pass success.

---

# 14. Speed / cost interpretation

## Direct control is currently too slow for production

RoboICL-style direct control can require dozens of GPT calls per episode.

Published wall times for direct frontier-model control can reach many tens of minutes depending on task and reasoning setting.

This is not yet a routine production controller.

Use direct control as:

- experimental generality probe,
- fallback for OOD tasks,
- evidence that frontier reasoning can physically recover.

## Hybrid is better, but not yet selective enough

The current GPT-as-Policy hybrid roughly halves the number of action segments versus Direct in its selected evaluation and substantially reduces tokens.

But it still reviews each proposal decision.

The eventual commercial architecture should probably be:

```text
fast policy continues autonomously
        ↓
cheap monitor / confidence / progress detector
        ↓ only on anomaly
GPT-6 wakes up
        ↓
replan / correct / recover
        ↓
fast policy resumes
```

This is **later**.

Do not build the gate tonight unless everything else is already working.

---

# 15. Why this is different from simulation-first deployment companies

Do not pitch the product as:

> “We build better robot simulations.”

Do not pitch it as:

> “We benchmark policies.”

The sharper story:

> **Simulators can tell you where a nominal policy fails. We are trying to make the robot adapt and keep working when reality differs from the nominal case.**

Potential longer-term loop:

```text
site / workflow
→ optional digital twin
→ initial execution
→ failures / interventions
→ adaptive frontier-model recovery
→ verified successful traces
→ reusable memory / skills / post-training data
→ cheaper routine policy
→ frontier reasoning only on exceptions
```

That compounds value from deployments.

---

# 16. Demo storyboard

A strong 30–60 second demo could be:

### Frame 1 — hard technical task

```text
TASK:
Install the GPU into the target slot.
```

Caption:

```text
No task-specific fine-tuning.
No hand-written task script.
No privileged simulator state.
```

### Frame 2 — routine action

Show FLUX proposal / GPT approval, or direct RoboICL action.

### Frame 3 — non-nominal physical event

Examples:

- connector misaligned,
- part slips,
- insertion only partial,
- object moves from expected pose.

### Frame 4 — explicit memory/recovery

Overlay:

```text
Previous action:
approach + insert

Observed result:
connector not seated

Next decision:
re-align from current visual state
```

### Frame 5 — recovery

Robot adjusts from the new state.

### Frame 6 — success

Native environment evaluator indicates task success.

### End card

> **Adaptive execution for physical AI**  
> Act → observe → learn from the outcome → recover  
> No reset. No new robot program.

If accelerated, include e.g.:

```text
Playback: 4×
```

---

# 17. What not to claim

Do not claim:

- production reliability from a cherry-picked successful rollout,
- general sim-to-real transfer before testing real hardware,
- that FLUX is universal,
- that GPT is fast enough for routine motor control,
- that the hybrid calls GPT only on 14.4% of decisions,
- that a benchmark result proves ROI,
- that memory equals parameter learning,
- that a single successful episode constitutes a robust deployment.

The demo is an existence proof / product-direction artifact.

The honest claim is:

> **This architecture can sometimes recover from non-nominal physical state using multimodal context rather than requiring a newly authored task program or a target-task weight update.**

---

# 18. Later experiments, in priority order

Only after the immediate demo:

## A. Selective GPT invocation

Build a cheap gate so FLUX can execute multiple segments without GPT when behavior is nominal.

Possible signals:

- policy entropy/confidence,
- VLM progress verifier,
- visual change consistency,
- action/proposal consistency,
- repeated no-progress,
- contact/force anomaly,
- state novelty.

Goal: move from ~dozens of GPT calls toward a small number of exception calls.

---

## B. Context compression / procedure memory

Convert raw past interactions into compact reusable procedural memory while keeping key images/raw references.

Test:

```text
raw RoboICL anchors
vs
compressed execution memory
vs
raw + compressed
```

Metrics:

- success,
- token count,
- latency,
- transfer to changed geometry.

---

## C. Successful episode → in-context reference

Once a task succeeds:

```text
successful trace
→ reference example
→ new layout / related task
```

Test whether the next deployment requires fewer GPT calls.

Important: do not assume exact motor trajectory is transferable. Prefer extracting procedure + key execution examples.

---

## D. Dynamic Hybrid → Direct fallback

Only after both modes work independently.

Example rule:

```text
FLUX hybrid attempts N times without progress
→ escalate to Direct RoboICL
→ recover / solve unusual state
→ optionally return to FLUX
```

---

## E. Qwen-inspired action representation

Source:

- https://arxiv.org/pdf/2606.17846

Potential hypothesis:

GPT direct control may improve if relative actions are expressed in a visually aligned / camera-aligned frame instead of world-frame deltas.

Not tonight.

---

## F. GraspGenX specialist primitive

Sources:

- https://graspgenx.github.io/
- https://github.com/NVlabs/GraspGenX

Potential role:

```text
learned policy struggles to regrasp novel object
→ invoke GraspGenX
→ obtain robust grasp
→ hand control back
```

Not core to screw/insert/fold behavior.

---

## G. Code-generation fallback

EmbodiedSWE-style agent code remains useful when neither learned policy nor direct embodied control can solve the task.

Treat it as:

```text
last-resort commissioning / data-generation mechanism
```

not the normal physical execution loop.

---

# 19. Suggested repository/worktree organization

Do not fork every upstream project into one monolith immediately.

Suggested integration repo:

```text
adaptive-physical-execution/
├── README.md
├── configs/
│   ├── tasks/
│   ├── controllers/
│   └── reasoning/
├── adapters/
│   ├── embodiedswe_env.py
│   ├── roboicl_direct.py
│   ├── gpt_as_policy_direct.py
│   └── flux_hybrid.py
├── memory/
│   ├── interaction_record.py
│   ├── anchored_memory.py
│   └── compact_summary.py        # later
├── execution/
│   ├── bounded_eef.py
│   ├── policy_chunk.py
│   └── receipts.py
├── runners/
│   ├── run_direct_roboicl.py
│   ├── run_direct_gpt_policy.py
│   └── run_hybrid_flux.py
├── analysis/
│   ├── summarize_run.py
│   ├── compare_runs.py
│   └── render_demo.py
└── upstream/
    ├── RoboICL/                  # submodule / sibling clone
    ├── GPT-as-Policy/
    ├── flux-action/
    └── EmbodiedSWE/
```

Prefer thin adapters to invasive edits of upstream repositories.

Preserve upstream commit SHAs in every run manifest.

---

# 20. Minimal run manifest

Each rollout should produce:

```json
{
  "task": "...",
  "robot": "franka",
  "env_commit": "...",
  "controller": "roboicl_direct | gpt_policy_direct | flux_gpt_hybrid",
  "controller_commit": "...",
  "model": "gpt-6-astra",
  "reasoning_effort": "medium",
  "motor_policy": "flux-3-action-droid",
  "seed": 0,
  "privileged_policy_inputs": false,
  "started_at": "...",
  "wall_seconds": 0,
  "simulated_seconds": 0,
  "gpt_calls": 0,
  "token_usage": {},
  "success": false,
  "score": null,
  "video_path": "...",
  "history_path": "..."
}
```

The experiment should be reproducible enough that a good clip is not detached from its actual run.

---

# 21. Stop conditions / decision rules

Because time is limited, aggressively kill bad branches.

## RoboICL Direct

Continue if:

- it makes visually sensible progress,
- recovers from at least one error,
- Medium reasoning appears adequate.

Stop / escalate if:

- repeated axis/geometry mistakes,
- no task progress after several model turns,
- action interface mismatch dominates behavior.

## GPT-as-Policy Direct

Keep as comparison.

Do not spend large time optimizing if RoboICL is clearly better on the target task.

## FLUX hybrid

Continue if:

- FLUX proposals are at least directionally competent,
- GPT can detect obviously bad proposals,
- task progresses faster than direct control.

Stop FLUX integration if:

- embodiment/action conversion is fundamentally mismatched,
- proposal outputs are nonsensical in the selected EmbodiedSWE configuration,
- adapter work is becoming a training project.

In that case, use RoboICL Direct for the demo and retain hybrid as next-step architecture.

---

# 22. Immediate priority order

If only one external agent is implementing:

1. **Clone/validate RoboICL upstream.**
2. **Clone/validate GPT-as-Policy Direct + Hybrid upstream.**
3. **Clone EmbodiedSWE and run target PC assembly environment.**
4. **Build non-privileged EmbodiedSWE observation/action adapter.**
5. **Port RoboICL zero-shot first.**
6. **Run GPU task at Medium.**
7. **Port GPT-as-Policy Direct.**
8. **Run same task at Medium.**
9. **Bring up FLUX DROID inference.**
10. **Adapt GPT-as-Policy Hybrid to FLUX + EmbodiedSWE.**
11. **Add RoboICL-style interaction records/memory to hybrid.**
12. **Run GPU / RAM / GPU+RAM.**
13. **Select the best recovery-containing successful clip.**
14. **Render an honest accelerated demo with model/controller labels.**

If multiple agents can work in parallel:

### Agent A — EmbodiedSWE adapter

Own:

- GPU/RAM environment,
- policy-safe observations,
- action execution,
- evaluator,
- recording.

### Agent B — RoboICL Direct

Own:

- faithful direct policy loop,
- Medium/XHigh configuration,
- memory,
- action serialization.

### Agent C — Hybrid

Own:

- GPT-as-Policy runtime,
- FLUX inference,
- proposal adapter,
- execution history,
- reviewer.

### Agent D — experiment/video

Own:

- manifests,
- token/latency logging,
- run launcher,
- dashboards,
- stitched/speed-labelled videos.

---

# 23. Current working thesis

The thesis to preserve during implementation:

> **Robot deployment should not require a robotics engineer to author a new program every time physical reality deviates from the nominal plan. A frontier model should be able to use current perception, execution history, and existing motor priors to recover online; successful experience should then make future execution cheaper.**

The demo is meant to test and communicate this thesis.

It is **not** primarily an academic benchmark submission.

---

# 24. Full source index

## Immediate implementation sources

### RoboICL
- Paper: https://arxiv.org/abs/2609.34261
- Project: https://mosi-ai.github.io/RoboICL-GPT6-Astra.github.io/
- GitHub: https://github.com/Mosi-AI/RoboICL

### GPT-as-Policy
- Report: https://anonymous-report-421.github.io/public-website/?lang=en&view=1
- GitHub: https://github.com/anonymous-report-421/GPT-as-Policy

### FLUX 3 Action
- Model page: https://bfl.ai/models/flux-3-action
- GitHub: https://github.com/black-forest-labs/flux-action
- HF collection: https://huggingface.co/collections/black-forest-labs/flux-3-action
- DROID checkpoint: https://huggingface.co/black-forest-labs/flux-3-action-droid

### EmbodiedSWE / RoboBench
- Project: https://embodiedswe.github.io/
- GitHub: https://github.com/EmbodiedSWE/EmbodiedSWE
- Paper: https://arxiv.org/abs/2609.27308

## Related evaluation/context

### RoboDojo GPT-6 / RoboProbe
- GPT-6 evaluation: https://robodojo-benchmark.com/report/gpt-6-astra-eval
- RoboProbe: https://github.com/RoboProbe/RoboProbe
- Related paper: https://arxiv.org/pdf/2609.24170

### General Deployment
- https://generaldeployments.com/

## Later research ideas

### Qwen representation alignment
- https://arxiv.org/pdf/2606.17846

### GraspGenX
- https://graspgenx.github.io/
- https://github.com/NVlabs/GraspGenX

---

# 25. Final instruction to the implementing agent

Do not optimize for elegance before there is a working physical loop.

The first decisive question is:

> **Can a non-privileged, context-aware GPT-6 controller or FLUX+GPT hybrid solve one hard EmbodiedSWE PC-assembly task—and especially recover after the physical state changes—without writing a new task program or fine-tuning a task-specific policy?**

Get that working first.

Then compare latency, memory design, reasoning effort, and policy-vs-direct execution.

A single strong, well-recorded recovery episode is more valuable for the immediate objective than a broad but shallow benchmark sweep.
