# Runbook: from this ZIP to a real experiment

## 1. Validate the CPU package first

From the package root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
physical-exec smoke --output runs/cpu_smoke
```

No network, API key, GPU, or simulator is used by the tests after package dependencies
are installed. Smoke files are not physical results. New output directories are mandatory.

## 2. Fetch the exact source revisions

```bash
python scripts/bootstrap_upstreams.py                        # show plan
python scripts/bootstrap_upstreams.py --execute              # fetch four pinned repos
python scripts/bootstrap_upstreams.py --verify-only
```

The build container could read GitHub through its connector but could not resolve github.com
from `git clone`. This is why you receive a pinned source-fetcher, not four pretend clones.
The fetcher refuses dirty/mismatched existing checkouts and leaves LFS smudging off. It does
not install packages or fetch weights. Add `--submodules` only when needed; some upstream
native workflows need large pinned submodule trees.

Read `upstream.lock.json` before changing versions. Changing a pin means requalifying its
API. Use separate checkouts/worktrees for native baseline modifications.

## 3. Keep three Python environments separate

| Process | Interpreter / environment | Purpose |
|---|---|---|
| Orchestrator | Core package Python ≥3.11 | API calls, context, logging, experiment loop |
| Simulator | Upstream EmbodiedSWE Isaac environment, Python 3.11 | Physics, camera capture, robot control, native scorer |
| FLUX | Upstream FLUX environment, Python 3.12 | GPU motor-policy inference |

The inspected EmbodiedSWE setup uses Isaac Sim 5.1 / Isaac Lab 2.3.2. The inspected FLUX
setup lists its own Torch/CUDA/NATTEN versions. Follow their **pinned docs**, rather than
trying to force both into one virtual environment.

Simulator setup, on your GPU machine:

```bash
cd upstream/EmbodiedSWE
./scripts/bootstrap_isaaclab_5_1.sh
# Review and accept the Isaac Sim license yourself before running headlessly.
# Set OMNI_KIT_ACCEPT_EULA=YES only after that acceptance.
```

Our worker needs `numpy`, `Pillow`, and `httpx` in the simulator interpreter. Install the
core package there with `--no-deps` after confirming those small dependencies are available;
do not inadvertently replace the simulator's Torch/NumPy stack:

```bash
/path/to/EmbodiedSWE/.venv/bin/python -m pip install --no-deps -e /absolute/path/to/adaptive_physical_execution
```

A graphics-capable GPU/driver setup is required for the simulator. A large compute GPU being
available does not establish that the Isaac renderer works on that machine. Inspect the
upstream requirements and prove camera capture before renting a large training node for
this job. The motor-policy worker may be on another machine; use SSH forwarding.

## 4. Generate separate worker tokens

```bash
export PHYSICAL_EXEC_SIM_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(24))')"
export PHYSICAL_EXEC_FLUX_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(24))')"
```

Copy the corresponding token securely into the worker's environment. Never put tokens in
source, command-line arguments, reports, or public logs. Workers bind **127.0.0.1 only**.
For remote hosts, SSH-forward their ports. There is no public unauthenticated robot RPC.

## 5. Start one simulator, then inspect sensors before any model request

```bash
/path/to/EmbodiedSWE/.venv/bin/python scripts/serve_embodiedswe.py \
  --repo /absolute/path/to/upstream/EmbodiedSWE \
  --task configs/tasks/pc_gpu.json \
  --record-dir runs/gpu_sensor_recordings \
  --port 8765 --headless
```

In the core environment:

```bash
physical-exec capture --sim-url http://127.0.0.1:8765 \
  --seed 0 --output runs/gpu_capture
```

Inspect `camera_index.json`, the three PNGs, `metadata.json`, and `observation.json`.
The default two external camera placements are initial **operator trial settings**, not
validated reconstructions of DROID calibration. Check the target, gripper, and work area are
visible. Edit `configs/tasks/pc_gpu.json` as needed, restart, and recapture.

The reset performs a robot-only URDF FK comparison against the simulator's measured
`panda_hand` frame. A mismatch is a hard failure. Do not silence it: check robot root,
joint order, hand-frame offsets, and quaternion conventions.

**One episode per simulator worker. Restart after capture before a new paid rollout.**
Capture intentionally consumes the reset; it cannot be silently reused as a fresh trial.

## 6. Direct-A: first low-budget live-model trial

Set your API key in an environment variable. Supply the **complete endpoint** and exact
model identifier authorized for your account. The package has not tested any live model.

```bash
export OPENAI_API_KEY='YOUR_KEY'  # preferably inject through your normal secret manager
export MODEL_ID='YOUR_AUTHORIZED_MODEL_ID'
export RESPONSES_ENDPOINT='https://YOUR_AUTHORIZED_HOST/v1/responses'
```

On a **fresh** simulator worker:

```bash
physical-exec run --task configs/tasks/pc_gpu.json --mode direct_roboicl \
  --model "$MODEL_ID" --endpoint "$RESPONSES_ENDPOINT" \
  --reasoning medium --horizon 5 \
  --max-decisions 3 --max-control-steps 15 --max-wall-seconds 180 \
  --output runs/gpu_direct_smoke --allow-paid
```

This tests the paid API and closed-loop bridge, not task performance. Exit code 2 is normal
for a budget-limited incomplete episode. Inspect `result.json` and `report.html`.

The Responses client uses a strict `Act` function call, explicit bounded history, and no
shell tools. If your authorized provider does not support this Responses schema, fix the
provider adapter explicitly; there is no silent fallback to another model/provider.

Then run a longer fresh trial, for example 50 decisions / 900 wall seconds. Medium vs
high/xhigh is a measured experiment, not an assumed 2× latency tradeoff. Record refusals,
truncated output, timeouts, and unsuccessful attempts. A low output cap can truncate
reasoning before an action; increase it deliberately if that is the measured issue.

## 7. Direct-B reference port

Run another fresh worker and replace the mode:

```bash
physical-exec run --task configs/tasks/pc_gpu.json --mode direct_reference \
  --model "$MODEL_ID" --endpoint "$RESPONSES_ENDPOINT" \
  --reasoning medium --horizon 3 \
  --max-decisions 50 --max-wall-seconds 900 \
  --output runs/gpu_direct_reference --allow-paid
```

This uses short absolute EEF targets with full history subject to explicit image/text
budgets. It is not the full native GPT-as-Policy Codex agent. Compare as an implementation
port, not as an exact paper reproduction. Context-budget exhaustion ends the run rather
than silently dropping evidence. Raise `--max-images` only with an explicit cost decision.

## 8. Bring up FLUX independently

Follow the pinned `upstream/flux-action/docs/setup.md`. The inspected source separates
DROID, SO-101, full-training exports, and optimized package variants. Use **DROID BF16 eager**
first. Download the complete selected policy package and cache its referenced encoders.
We do not download weights or accept licenses for you.

Start the worker inside FLUX's environment:

```bash
/path/to/flux-action/.venv/bin/python scripts/serve_flux.py \
  --checkpoint /absolute/path/to/complete-local-droid-package \
  --device cuda:0 --port 8766
```

The worker imports `flux_action.policy.FluxActionPolicy`, loads once, and serves repeated
predictions. Its three inputs must be distinct real views; duplicate/padded cameras are
rejected. The model package controls its inference settings. Compilation is opt-in.

After a simulator capture, probe FLUX **without executing its output**:

```bash
physical-exec probe-flux --task configs/tasks/pc_gpu.json \
  --sim-url http://127.0.0.1:8765 --flux-url http://127.0.0.1:8766 \
  --output runs/gpu_flux_probe
```

Inspect `proposal.json`: shape, action magnitudes, gripper range, robot-only FK path,
and generic bounds. This can fail because a policy is out of distribution even when
its interface is correct. Do not weaken bounds merely to make a video.

The chosen control rate is an explicit trial setting. The package does not prove it is
matched to all FLUX checkpoint variants. Verify timing and dataset conventions before
interpreting behavior. No arbitrary retiming or normalization fallback is performed.

## 9. Hybrid trial

Restart the simulator. Keep the FLUX worker warm:

```bash
physical-exec run --task configs/tasks/pc_gpu.json --mode hybrid \
  --model "$MODEL_ID" --endpoint "$RESPONSES_ENDPOINT" \
  --reasoning medium --horizon 8 \
  --max-decisions 3 --max-wall-seconds 180 \
  --ack-experimental-flux --output runs/gpu_hybrid_smoke --allow-paid
```

Then extend the budget on a fresh run. The initial hybrid reviews every proposal. It
executes a fresh prefix or an explicitly bounded EEF correction. It does not autonomously
switch to a different controller for the rest of the episode.

**If FLUX makes incoherent proposals, retain Direct-A as the principal task-solving path.**
The package is not evidence that the DROID policy covers GPU/RAM insertion.

## 10. Memory/reference experiments

Anchored interaction memory is enabled by default for Direct-A and Hybrid. For a memory
ablation, use `--memory full` on otherwise matched runs. The exact RoboICL anchor selector
retains initial/selected/latest executed chunks and marks gaps; it does not fabricate
failure labels or treat model summaries as observed facts.

After a genuine natively successful simulator run:

```bash
physical-exec run ... --reference-run runs/previous_native_success
```

The loader verifies trace/frame integrity, requires the same robot, control period, and
EEF frame, and rejects software fixtures. Same task is required by default;
`--allow-related-reference` explicitly permits a different task instruction. No
cross-embodiment retargeting is implemented. A successful trace is an example—not proof
that copying its motor geometry will generalize.

Compact model-authored summaries have a typed memory hook, but **no automatic summary
model or demonstrated compression improvement is implemented**. Preserve that as a later
ablation instead of mixing it into the first comparison.

## 11. Native upstream reference route

Use the exact pinned RoboICL code when testing its original dual-arm RoboDojo setting.
First replace the upstream third-party endpoint explicitly:

```bash
python scripts/make_native_roboicl_profile.py --repo upstream/RoboICL \
  --endpoint "$RESPONSES_ENDPOINT" --model "$MODEL_ID" \
  --reasoning medium --shots 0 --output runs/native_roboicl_profile.json
```

In the upstream setup, configure its separate simulator/policy interpreters and fetch the
pinned assets/submodules. Then run its documented `--dry-run`, `--capture-only`, and finally
a paid episode with this absolute profile path. The package does not claim the native
RoboDojo environments are installed or that its transport accepts every provider.

For the original GPT-as-Policy full Codex runtime, use its own pinned README and
`hybrid_rollout/robodojo/skill/run.py`. It needs its simulator and Codex account configuration;
its baseline pins xhigh in more than one configuration/validation location. Do not change
one string and report a medium experiment unless the launched manifest confirms the setting.
This ZIP does not silently alter that baseline or your Codex home.

## 12. Campaigns, reports, video

```bash
python scripts/run_matrix.py --sim-python /path/to/EmbodiedSWE/.venv/bin/python \
  --sim-repo upstream/EmbodiedSWE \
  --tasks configs/tasks/pc_gpu.json configs/tasks/pc_ram.json \
  --modes direct_roboicl hybrid --seeds 0 --reasoning medium \
  --model "$MODEL_ID" --endpoint "$RESPONSES_ENDPOINT" \
  --output runs/first_campaign
```

This prints a plan only. Add `--execute --allow-paid --ack-experimental-flux` after
individual qualification. It launches one fresh owned simulator per case, preserves
failures, and never automatically rerolls a failed case. The FLUX worker remains a separately
managed process. A model token cap is a returned-usage cutoff, not a guaranteed dollar cap;
a single request may cross it. Use provider-side spending limits as well.

```bash
physical-exec compare runs/gpu_direct runs/gpu_hybrid --output runs/comparison
physical-exec report runs/gpu_hybrid
physical-exec verify-trace runs/gpu_hybrid
```

Boundary-observation HTML is not a continuous video. For true per-control-latch frames:

```bash
python scripts/render_control_video.py runs/simulator_recordings/EPISODE_ID \
  --view left --speed 4 --output runs/demo.mp4              # show command
# Add --execute to render with installed FFmpeg.
```

The video label explicitly says **simulation**, the simulated-time playback factor,
**model waits excluded**, and grasp assistance if enabled. Wall time remains in the run
report. Edited playback is not evidence of real-time control.

For the business demo, distinguish a successful example from deployment reliability.
“No online task-code edits or task-specific fine-tuning during this rollout” may be
supported; “no engineering,” “works in the real world,” and “ROI improved” are not yet supported.
