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

The system Python 3.14 environment failed during ensurepip; the separate
Python 3.11 environment works. Generated environments and runs are ignored.
The imported release manifest records the original package, not future edits.
Local smoke output: `runs/local_cpu_smoke_20260929/`.

## Priority 1: source and integration review (CPU, no paid calls)

- [ ] Fetch the four pinned upstream repositories using
  `scripts/bootstrap_upstreams.py --execute`; verify commits and audited blobs
  with `--verify-only`. Keep them in ignored `upstream/` directories.
- [ ] Check licenses and redistribution conditions for each selected checkpoint,
  encoder, asset and dependency. Preserve source provenance.
- [ ] Compare the real pinned APIs with both workers: imports, constructor
  arguments, return types, checkpoint layouts and expected config files.
- [ ] Inspect the actual Franka URDF: root and hand frames, joint ordering,
  joint limits, quaternion convention, gripper aperture and FK/IK mapping.
- [ ] Confirm simulator joint-PD execution timing against FLUX's training action
  rate and chunk semantics. Record any mismatch before interpreting behavior.
- [ ] Verify FLUX's required image sizes, three-view ordering, preprocessing,
  state normalization, encoder dependencies and gripper convention from source.
- [ ] Review actor observation construction and prompt serialization for hidden
  object poses, native success scores, scene metadata and evaluator leakage.
- [ ] Review shutdown, request timeout, partial execution, stale observation and
  duplicate-command handling against real worker behavior, supplementing mocks
  where evidence reveals gaps.

Stop here to fix concrete integration defects; do not use extra component tests
as a substitute for the eventual simulator experiment.

## Priority 2: reproducibility and experiment preparation (CPU)

- [ ] Record resolved CPU dependency versions and verify wheel installation in
  a fresh environment; confirm bundled third-party license inclusion.
- [ ] Check GitHub CI on Python 3.11, 3.12 and 3.13.
- [ ] Exercise capture/probe/report/compare/trace CLI paths using fixtures where
  supported, and inspect the generated HTML and video labels.
- [ ] Dry-run a small campaign; confirm unique output directories, seeds, budgets,
  exact model/effort settings and cleanup of owned worker processes.
- [ ] Write the initial experiment matrix: one `pc_gpu` capture, three Direct-A
  decisions, FLUX proposal-only probe, then a bounded Hybrid trial.
- [ ] Predefine success via the native evaluator, maximum decisions/control
  steps/wall time, failure categories, and recovery without a reset.
- [ ] Specify matched task/seed/observation/control budgets for later Direct-A,
  Direct-B and Hybrid comparisons; record unavoidable context differences.
- [ ] Plan the memory comparison after a verified successful trace exists:
  interaction memory versus reference demonstrations, including geometry shift.
- [ ] Prepare the demo storyboard and report fields: simulated time, wall time,
  model wait, calls, cached/uncached tokens, interventions and grasp assistance.
- [ ] Define the backup manifest and resume procedure before the next rental:
  source revision, dependency versions, configs, model identifiers/checksums,
  run artifacts and important uncommitted changes; exclude credentials.

## Optional before GPU: live API and artifact staging

These need network/account access, and live model tests spend API budget, but
none requires a GPU. No paid calls have been made by this import.

- [ ] Verify the chosen endpoint/model supports images, Responses tool schemas,
  configured reasoning effort and usage reporting with a tightly bounded call.
- [ ] Use retained, appropriately labelled images to inspect visual inputs and
  prompt formatting. This can assess recognition/schema behavior, not control.
- [ ] Verify budget accounting, timeouts and provider errors against that endpoint.
- [ ] Identify the exact FLUX DROID BF16 checkpoint and all referenced encoders;
  estimate download/disk size and memory requirements from source/model metadata.
- [ ] Download approved weights/assets ahead of time if storage and transfer
  location make it worthwhile; record hashes. Loading them is still unverified.
- [ ] Prepare separate Linux simulator and FLUX install commands or build recipes,
  using the pinned dependency versions. Mac tests cannot validate CUDA/Isaac.
- [ ] Prepare SSH forwarding and secret injection templates without embedded keys.

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
