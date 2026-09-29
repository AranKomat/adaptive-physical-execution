# Before renting a 4090

Date: 2026-09-29. This is the operational checklist for the imported package.
The research hypothesis is Hybrid (FLUX + GPT + interaction memory); Direct-A
is the first short integration trial because it does not depend on FLUX.
Direct-A is also the preferred direct-control reference. Starting with its
plumbing does not change the main research hypothesis.

## Verified locally

- [x] Extract release into a separate project; retain original licenses and notices.
- [x] Verify all 109 files against the supplied release manifest.
- [x] Confirm `docs/ORIGINAL_HANDOFF.md` matches the separately supplied handoff.
- [x] Check source for common credential patterns and personal-context strings.
- [x] Install a separate Python 3.11.14 CPU environment (`.venv-cpu`).
- [x] Reproduce all 86 tests: 86 passed in 4.30 seconds on this Mac.
- [x] Run all three software-fixture smoke modes successfully.
- [x] Fetch all four pinned upstream repositories and verify audited Git blobs.
- [x] Run the supplied release verifier after source preparation.
- [x] Compile the package, scripts, and relevant pinned Python source trees.
- [x] Verify the public CPU CI workflow completed successfully on the first push.

The system Python 3.14 environment failed during ensurepip; the separate
Python 3.11 environment works. Generated environments and runs are ignored.
The imported release manifest records the original package, not future edits.
Local smoke output: `runs/local_cpu_smoke_20260929/`.

## Priority 1: source and integration review (CPU, no paid calls)

- [x] Fetch and verify the four pinned upstream repositories. Results are in
  ignored `upstream/` directories and the exact commits are recorded in
  `upstream.lock.json`.
- [x] Inspect project licenses and notices. RoboICL is MIT, EmbodiedSWE is
  Apache-2.0, and the other project code retains its upstream terms. The FLUX
  checkpoint has a separate FLUX Kommunity License; its commercial/production
  and robotics-use terms must be reviewed before using it beyond research.
- [x] Compare the pinned APIs with both workers. The FLUX adapter matches the
  pinned `FluxActionPolicy.from_pretrained` / `prepare_inference` /
  `predict_action_chunk` interface. The simulator adapter matches the pinned
  `load_sim` / `EvalSim` contract. Runtime imports remain GPU-environment gates.
- [x] Inspect the pinned Franka URDF and robot source: the adapter requires the
  seven `panda_joint1` through `panda_joint7` order, uses `panda_hand`, and
  validates FK against the simulator at reset.
- [x] Record the timing mismatch as an explicit experiment condition: FLUX DROID
  data is 15 Hz and emits 32 absolute joint targets; the adapter requests the
  simulator at 15 Hz, but this has not yet been physically qualified.
- [x] Verify FLUX's source contract: three separate `wrist/left/right` RGB inputs
  at `360x640`, seven joint radians plus closed gripper fraction, absolute
  joint output, and external encoder references. The adapter converts gripper
  closedness to the package's open-fraction convention exactly once.
- [x] Review the actor observation and prompt boundary. Only task text, supplied
  RGB, joints, EEF/aperture, timing, receipts, and robot-only FK enter policy
  context; evaluator success/progress and object coordinates stay host-side.
- [x] Review shutdown, timeout, partial-execution, stale-observation, duplicate
  command, and ambiguous-execution handling. CPU tests cover these contracts;
  simulator timing and process shutdown remain GPU validation gates.

Stop here to fix concrete integration defects; do not use extra component tests
as a substitute for the eventual simulator experiment.

## Priority 2: reproducibility and experiment preparation (CPU)

- [x] Record resolved CPU dependency versions in the local 3.11 environment;
  the wheel install and bundled RoboICL license were verified.
- [x] Check CI coverage. Python 3.11 and 3.13 were run locally (`86 passed`);
  the pushed GitHub workflow completed successfully and covers 3.11, 3.12, 3.13.
- [x] Exercise fixture smoke, trace verification, HTML report regeneration,
  comparison export, doctor, compile, and release-verification paths. Capture
  and FLUX probe require the GPU workers by design.
- [x] Dry-run a two-case `pc_gpu` campaign. It records two cases, medium effort,
  seed 0, 100 maximum model decisions, and 900 seconds per case without API or
  simulator startup.
- [x] Record the initial experiment matrix in `RUNBOOK.md`: capture, three
  Direct-A decisions, proposal-only FLUX, then bounded Hybrid.
- [x] Define the initial native-evaluator success boundary, budgets, failure
  classes, no-reset recovery requirement, and host-only evaluator reporting.
- [x] Specify matched task/seed/observation/control budgets and context
  differences in the runbook and task/controller configs.
- [x] Specify the future interaction-memory versus reference-demonstration
  comparison, including geometry shift and the requirement for a native success
  before a trace can be reused.
- [x] Prepare the demo fields and labels: simulated/wall time, model wait,
  calls, cached/uncached/reasoning tokens, interventions, and grasp assistance.
- [x] Define backup and resume requirements in the runbook and operator
  checklist: source revisions, environment versions, configs, model IDs and
  hashes, artifacts, and no credentials.

## Optional before GPU: live API and artifact staging

These need network/account access, and live model tests spend API budget, but
none requires a GPU. No paid calls have been made by this import.

- [ ] Verify the chosen endpoint/model supports images, Responses tool schemas,
  configured reasoning effort and usage reporting with a tightly bounded call.
- [ ] Use retained, appropriately labelled images to inspect visual inputs and
  prompt formatting. This can assess recognition/schema behavior, not control.
- [ ] Verify budget accounting, timeouts and provider errors against that endpoint.
- [x] Identify the exact FLUX DROID checkpoint and referenced encoder model from
  the pinned docs. Hugging Face metadata reports approximately 13.9 GB for the
  default/GD weights and 7.1 GB for the FP8r/GD-FP8r variants. The model card
  reports the FLUX Kommunity License; no license acceptance or weight download
  was performed.
- [ ] Download approved weights/assets ahead of time. This is optional and
  remains deliberately deferred until the license/use choice and target Linux
  cache location are settled; hashes can then be recorded.
- [x] Prepare separate Linux simulator and FLUX install commands in `RUNBOOK.md`.
  The pinned FLUX project requires Python 3.12 and CUDA 12.8 wheels on Linux;
  EmbodiedSWE and the orchestrator remain separate environments.
- [x] Prepare SSH forwarding and secret-injection commands in `RUNBOOK.md`; no
  keys or tokens are embedded in source, logs, or the public repository.

## Requires the GPU host

- Isaac Sim installation/runtime qualification with the actual NVIDIA driver.
- Three real camera renders with visible target, gripper and work area.
- Simulator-versus-URDF FK qualification and physical action tracking.
- FLUX weight loading, measured peak VRAM and cold/warm latency.
- Co-residency measurements for Isaac and FLUX on the 24 GB 4090. Fit is unknown;
  do not assume a second GPU is necessary or that one is sufficient.
- Contact, grasp, insertion and independently evaluated task success.
- Recovery after a physical disturbance, matched controller comparisons and
  demonstration-memory benefits.

## Rental start gate

At minimum finish source verification, fix known adapter/API mismatches, choose
the exact checkpoint and model endpoint, and prepare commands/output budgets.
Then rent one graphics-capable 4090 and run capture -> Direct-A plumbing -> FLUX
proposal-only -> Hybrid. Broader model searches, post-training, dynamic mode
switching and memory compression remain later work.

See `RUNBOOK.md`, `SOURCE_AUDIT.md`, `IMPLEMENTATION_STATUS.md` and
`ORIGINAL_HANDOFF.md` for details. CPU validation provides no robotics success
evidence, and the old project's privileged repair scores do not transfer here.
