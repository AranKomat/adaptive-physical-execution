# Adaptive Physical Execution

**CPU-tested integration package for a sensor-grounded robotics experiment.**

This package implements the shared rollout core, three controller **ports**, a source-backed
EmbodiedSWE/Franka worker, a FLUX DROID worker, execution memory, recording, experiment tools,
and validation tests. **It does not contain a demonstrated solution to GPU/RAM insertion.**
No GPU, simulator, checkpoint, or paid model inference was run during this build.

The starting question is:

> Can a robot recover from a changed physical state using visual context and existing motor
> capabilities, without generating a new task script or updating policy weights?

## Start here

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
physical-exec doctor --task configs/tasks/pc_gpu.json
physical-exec smoke --output runs/cpu_smoke
```

Open `runs/cpu_smoke/direct_roboicl/report.html` and the other two reports.
**These are explicitly watermarked software fixtures, not robot demonstrations.**
The fixture simulates no physics and runs no learned model. It verifies that the software
records actions, observations, feedback, memory, errors, and termination coherently.

For actual GPU use, follow **[docs/RUNBOOK.md](docs/RUNBOOK.md)**. For the next coding agent,
start with **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** and
**[docs/SOURCE_AUDIT.md](docs/SOURCE_AUDIT.md)**.

## What is implemented

| Component | Implementation | Verification here |
|---|---|---|
| Direct A | Single-arm world-delta control, anchored execution memory, formal `Act` calls | CPU fixtures and tests |
| Direct B | Short absolute EEF targets with full bounded-by-budget history | CPU fixtures and tests |
| Hybrid | FLUX proposal → GPT review → accept / edit / bounded EEF correction / stop | Fake motor/model sources; tested gate and action semantics |
| RoboICL memory | **Exact upstream `LiveTrajectoryMemory` implementation**, with wrapper | Git-blob identity test; anchor/gap/receipt tests |
| Model transport | Explicit-endpoint Responses HTTP client; effort, usage and time budgets | Mock HTTP tests; **no live API call** |
| Simulator bridge | Uses EmbodiedSWE `load_sim` / `EvalSim`; Franka joint PD, robot-only FK/IK | Source inspection and CPU contract tests; **no Isaac launch** |
| FLUX bridge | Calls `FluxActionPolicy.from_pretrained` / `predict_action_chunk` | Image/state/gripper conversion tests; **no checkpoint loaded** |
| Recording | Append-only events, image checksums, command receipts, host-only evaluator results | End-to-end fixture tests |
| Reports | Self-contained HTML; CSV/JSON comparisons; FFmpeg command for per-latch video | HTML/CSV tested; no real rollout footage |
| Campaign | Fresh simulator process for each task/mode/seed; owned-process cleanup | CLI compilation and dry-run; GPU campaign untested |
| Upstreams | Exact commit lock plus explicit fetch/verification script | Pins inspected via GitHub; **full repositories not bundled** |

## Controller names deliberately say “port”

`direct_roboicl` is **not** a reproduction of the published RoboICL score. Its upstream
controller is dual-arm and RoboDojo-specific. This package adapts it to one Franka arm,
three real camera views, a different action schema, a new simulator, and a shared joint-PD
execution path. The anchor selection code itself is copied **without modification**.

`direct_reference` preserves the short absolute-target idea of GPT-as-Policy Direct, but
uses a constrained Responses client rather than the original full Codex agent with shell,
image/file tools, and persistent native conversation machinery.

`hybrid` preserves the report's main gate rule: a correction requires observed failure or
misaligned intent; uncertainty alone is insufficient. It replaces π₀.₅ with FLUX and can
use anchored history. It still asks GPT to review **every proposal**. It is not yet a
sparse-invocation runtime and has not been shown faster or more successful.

The native RoboICL profile utility and pinned checkouts let you keep an upstream reference
path instead of treating these ports as exact reproductions.

## Important source findings

**The GPU scene uses grasp assistance by default.** EmbodiedSWE's `PcGpuAssemblySceneCfg`
sets `grasp_weld=True`, and its PC tasks include authored fixtures and simplified contact
geometry. This package preserves the upstream environment and records its assistance
settings. “No privileged object state in the model prompt” is **not** the same as
“unassisted physics” or “sim-to-real validated.” See the audit before choosing demo captions.

**FLUX DROID is not an EEF controller.** It returns seven absolute joint targets plus a
**closed** gripper fraction. The shared contract uses an **open** fraction, so the boundary
converts it. There is no automatic cross-embodiment retargeting or claim that a DROID
checkpoint will solve PC assembly. Same robot name does not establish distribution match.

**No inherited third-party API gateway.** The published RoboICL profile contains a gateway
endpoint and model alias. This package requires your explicitly chosen endpoint and exact
model ID, plus `--allow-paid`. No keys are embedded, printed, or placed in a ZIP.

## Scope

Initial tasks: `assembly.pc_gpu.franka.joint`, `assembly.pc_ram.franka.joint`, then
`assembly.pc_gpu_ram.franka.joint`. `bulb` is an optional recovery-oriented task configuration.

No post-training, Unitree integration, GraspGenX, Qwen action-frame experiments,
autonomous cross-mode switching, real hardware support, or implicit online code generation.
The integration code is a host-authored control bridge—not a task-solving `solve(env)` script.

## Layout

```text
src/physical_exec/
  contracts.py, safety.py, geometry.py, kinematics.py
  memory.py, third_party/trajectory_memory.py
  controllers/ports.py
  providers/responses.py
  backends/{fixture,embodiedswe,flux}.py
  transport.py, runner.py, trace.py, reports.py, cli.py
scripts/
  bootstrap_upstreams.py             pinned fetch; plan-only by default
  make_native_roboicl_profile.py     explicit API routing for upstream reference
  serve_embodiedswe.py               Isaac Python 3.11 worker
  serve_flux.py                      FLUX Python 3.12 worker
  run_matrix.py                      explicit, bounded paid campaign
  render_control_video.py           labelled simulation-time video
configs/tasks/                       operator-visible task/camera trial settings
upstream.lock.json                   four audited commit pins
examples/cpu_fixture/                labelled, generated software-fixture evidence
```

The original requested plan is preserved as [docs/ORIGINAL_HANDOFF.md](docs/ORIGINAL_HANDOFF.md).
Where implementation choices or source findings differ, the audit and implementation status
are authoritative for **what this package actually does**.

## Provenance and licenses

Project-authored code is MIT licensed. The exact RoboICL memory helper retains its authors'
MIT license in `licenses/RoboICL-MIT.txt`. Upstream code, weights, simulator assets, and
commercial APIs retain their own licenses and terms. No weights, simulator assets, font
files, API credentials, private messages, or full upstream Git repositories are included.

**Simulation only. This is not a certified robot safety controller.**
