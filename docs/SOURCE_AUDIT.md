# Source audit and deliberate implementation differences

Audited 2026-09-29. All repository pins are in `../upstream.lock.json`.

Sources were read using the connected GitHub reader. A container `git clone` failed
because it could not resolve github.com. **No full upstream checkout was executed here.**
The local code and CPU tests are not represented as an upstream benchmark reproduction.

## 1. RoboICL

Repository: https://github.com/Mosi-AI/RoboICL

Pinned commit: `337e70591c3116d289b361aa61b38bce617831ef`.

Inspected paths:

- `roboicl/policy/trajectory_memory.py`
- `roboicl/policy/astra_policy.py`
- `roboicl/policy/dialogue_policy.py`
- `roboicl/policy/history_context.py`
- `roboicl/policy/anchored_cache.py`
- `configs/shared_harness.json`
- `configs/protocols/zero_shot_b25.json`

The complete `trajectory_memory.py` is vendored **verbatim**. Its Git blob is
`8542840fa65ff9fc8fcc5d3e15361473a51ae499`, verified by a CPU test. Its MIT copyright and
license are preserved. This implements deterministic fixed anchors, a rolling latest
chunk, explicit omitted intervals, idempotent capture, and immutable recorded intervals.

### What remains faithful

- Formal observation → action → receipt → resulting-observation history.
- Only committed execution becomes LIVE memory.
- Initial/current observations and selected historical chunks remain accessible.
- Gaps do not imply unobserved success or continuity.
- Model-authored statements are not promoted to measured object truth.
- World-frame incremental translations and rotations; incremental rotation left-multiplies
  the preceding commanded orientation.
- No gradient update or online task-program generation.

### What is a port, not a reproduction

| Published implementation | This package |
|---|---|
| Two RoboDojo arms | One Franka arm |
| Head/left-wrist/right-wrist triptych | Real wrist plus two exterior cameras, correctly labelled |
| RoboDojo action/controller pipeline | Shared EmbodiedSWE joint PD with robot-only URDF DLS IK |
| Native dual-arm `Act` action objects | Strict single-arm action schema |
| Published model/profile settings | Operator-selected endpoint/model/effort; medium initial trial |
| Provider-specific caching/reasoning-item machinery | Explicit Responses context; no private reasoning copied |
| Task-specific published horizons | Declared PC-task trial horizons, configurable |

The first port tests an architecture on a new environment. It cannot claim the paper's
score, precision, latency, or few-shot transfer. The native profile helper is provided for
running the original implementation separately after its dependencies are installed.

### API routing caveat

The inspected zero-shot profile explicitly names a third-party gateway and provider-specific
model alias. This is **not** permission to send the user's key/images there. Our live client
has no default endpoint and requires `--allow-paid`. The native profile generator writes a
new configuration with an explicitly supplied endpoint/model, without modifying the source.

## 2. GPT-as-Policy

Repository: https://github.com/anonymous-report-421/GPT-as-Policy

Pinned commit: `8f3d362b077d8efb77e2a7274d5b2c20e2243846`.

Key inspected sources:

- `hybrid_rollout/robodojo/skill/gate_prompt.md`
- `hybrid_rollout/robodojo/skill/run.py`
- `hybrid_rollout/robolab/skill/SKILL.md`
- `hybrid_rollout/settings.py` and the RoboDojo settings/configuration paths

The inspected original runtime is a persistent Codex agent with service tools plus native
file/image/shell capabilities. It uses xhigh in its published configuration. It reviews
policy proposals and preserves execution history. It is **not** an independent memoryless
reviewer on every frame.

Our hybrid preserves the core gate semantics:

1. Assess the previous actual execution separately from the next candidate intent.
2. Infer candidate motion from robot-only FK, not a simulated future of objects.
3. An edit or EEF takeover needs observed failure or misaligned intent.
4. Uncertainty alone does not authorize takeover.
5. The motor policy receives the original task instruction.
6. Every proposal is reviewed in the initial version.

We do **not** claim that swapping π₀.₅ for FLUX is a measured improvement, or that the
published fraction of GPT-corrected control steps equals the fraction of GPT calls.

Direct-B in this ZIP is a short absolute-target **reference port**, not the original
full Codex runtime. It intentionally has no shell/file-reading tool in the policy process.
This narrows the privileged-information attack surface but changes the experimental condition.

## 3. FLUX 3 Action

Repository: https://github.com/black-forest-labs/flux-action

Pinned commit: `e2dd1d8dbc5977b54315d61f7548c63c043d6d4f`.

Source: `docs/setup.md`, Python inference API and DROID sections.

Checkpoint: https://huggingface.co/black-forest-labs/flux-3-action-droid

The inspected DROID interface expects:

```text
images.wrist, images.left, images.right:
    synchronized B×3×360×640 RGB float tensors
state:
    B×8 = seven Panda joints in radians + gripper CLOSED fraction
task:
    one literal instruction per batch element
output:
    B×32×8 = seven absolute joint targets + gripper CLOSED fraction
```

The package's canonical gripper is OPEN fraction, so the adapter inverts exactly once on
each DROID boundary. It does not reinterpret joint positions as EEF deltas or velocities.
It rejects missing/duplicated cameras, wrong embodiment/joint order, invalid action shapes,
nonfinite outputs, and out-of-range gripper values. It does not silently clip predictions.

Same Panda embodiment is insufficient to establish camera, dynamics, control-rate,
contact, or task-distribution compatibility. A successful API call is not evidence that
FLUX can install a GPU. The probe command therefore runs inference/FK **without execution**.

The local policy path prevents accidental selection of an unrelated Hub checkpoint. Its
referenced encoders may still need explicit caching under the upstream loader. No weights
or encoder licenses are bundled or accepted by this package.

## 4. EmbodiedSWE

Repository: https://github.com/EmbodiedSWE/EmbodiedSWE

Pinned commit: `d34837e99e5016525f0e9b6bb84791eb3d4b8162`.

Key sources:

- `robobench/README.md`: raw `env.step/reset` return `None`; raw environment is intentionally open.
- `vla/eval/sim.py`: `load_sim`, `EvalSim`, joint/closedness conventions, cameras, grader.
- `vla/eval/README.md`: paused simulation during inference, camera/label/controller caveats.
- `robobench/robots/franka.py`: Panda hand frame, joint ordering, controller modes.
- `robobench/suites/assembly/configs/envs.py`: registered PC-task names and fixtures.
- `robobench/suites/assembly/scenes/pc_gpu_assembly.py`: physics and grasp assistance.

### Existing environment layer reused

The integration uses `load_sim` / `EvalSim` rather than calling nonexistent Gym-style raw
observations. `EvalSim.obs()` provides images, robot joint state plus gripper closedness,
and privileged success/progress fields. The wrapper constructs a fresh, allowlisted
`Observation`; the evaluator fields remain in a separate host result and never enter GPT
memory or FLUX input.

The source's robot kinematic model, measured robot joints, and measured hand pose are used
for FK/IK. This is robot calibration/proprioception, not hidden object state. Future FK
previews do not step physics or query object trajectories.

### Important: physics assistance is real

The pinned GPU scene declares:

```python
grasp_weld: bool = True
```

It instantiates a `GraspWeldContract`. The scene also documents an authored slot fixture,
funnel-like geometry, and gripper-friendly holders in relevant presets. These may be
appropriate benchmark conventions, but they are **not proof of physically robust grasping**.

This release does not silently alter those mechanics. It records `grasp_weld` and the
preserved-defaults disclosure in the run manifest and recording metadata. The video utility
adds an assistance label when enabled. Turning assistance off should be a separately named,
qualified experiment; the package does not claim to have tested that variant.

### Low-level control and time

All three integration ports initially use the same upstream joint-PD actuator path.
Direct Cartesian commands are mapped by a small robot-only DLS IK implementation. This
helps isolate policy comparisons but is **not** the same as the upstream OSC/impedance
controller, RoboICL's motion stack, or a real robot's force-control interface. It may be
inadequate for threaded/contact-rich tasks; that is an experimental limitation.

The simulator is paused while a model is reasoning. Therefore a clip rendered from
control-latch frames hides waiting time unless labelled. Both wall time and simulated
time are recorded. No real-time control claim is made.

## 5. Deliberate exclusions

- No Unitree/in-house whole-body controller reconstruction.
- No target-task fine-tuning or policy improvement claims.
- No automatic inter-mode switching or cheap gate that skips GPT calls.
- No code-generating agent with access to simulator files during a policy episode.
- No GraspGenX complete-mesh shortcut, privileged object segmentation, or object-pose tool.
- No camera-frame action redesign or asserted benefit from context compression.
- No head-to-head benchmark/cost claim derived from mock data.

## 6. Security and evidence boundary

The constrained policy tool is `Act` only. Worker RPCs are fixed and authenticated on
loopback; local receipt retries are idempotent but the client never retries ambiguous
physical execution. A transport failure after an action may have executed ends the run.

This is a practical API boundary, **not a certified sandbox or robot safety guarantee**.
An operator controlling the simulator process can still change its physics or files.
Hash-linked logs and image checksums detect accidental inconsistency; without an external
signature/anchor they are not proof against a party rewriting the entire artifact.

API token totals distinguish cached input and reasoning-token subsets. Missing provider
usage is marked unknown/incomplete, not treated as proof of zero spend. No dollar estimate
is invented. Provider-side budget controls are recommended.
