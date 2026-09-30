# GPU capacity and driver compatibility check

Purpose: determine whether the prepared1920x1080 condition can run separately
without resetting the held GPU or disturbing another workload.

## Verified state

SSH host76.71.203.193:45579. Six simulator worker processes remain resident:
ports8765,8767,8768,8773,8774,8772. The current held worker103000/8772 returned
`5fc1330e1fb9410e9cc56d5c948ee0af:1754` from a fresh observation. No reset or
control action was issued. Fresh public observation copied locally to
`runs/gpu_driver_check1754_observe_20260930`. A checksum-only rsync comparison of
remote/local `runs/gpu_resume1754_flat_20260930` returned no differences.
This verifies critical RGB-D data, not every full per-step recording.

Default `nvidia-smi` failed with driver/library mismatch. Loaded kernel module:
580.95.05; installed NVML:580.178.04. The mismatch alone does not establish the
cause of any earlier slow motion or invalidate existing experiment results.

## Isolated diagnostic workaround

Downloaded the repository-provided package
`libnvidia-compute-580=580.95.05-0ubuntu1` (54.7MB), without installing it, to
`/workspace/adaptive-gpu-compat-580.95.05`. Extracted with `dpkg-deb -x` into its
`extracted` subdirectory. Running only the diagnostic with process-local
`LD_LIBRARY_PATH` restored NVML:

```bash
LD_LIBRARY_PATH=/workspace/adaptive-gpu-compat-580.95.05/extracted/usr/lib/x86_64-linux-gnu \
  nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader
```

| GPU | Used | Free |
| --- | --- | --- |
|0|23234MiB|848MiB|
|1|22164MiB|1918MiB|

No system package installation, reboot, driver unload, global environment change,
worker retirement, or change to the unrelated CPU workload occurred. This
diagnostic does not qualify a new CUDA/Isaac worker: rendering libraries and GPU
initialization would still need validation when capacity becomes available.

## Consequence for experiment sequence

Do not start a high-resolution worker under this capacity condition. No new model
calls or physical experiments ran; no phase completed. A separate worker needs
an explicit resource choice: back up/retire a selected older simulator episode
(losing its live physics state), or use another instance. The held8772 episode
must remain protected. Do not silently retire an unrelated episode to fit the
new test. The proposed candidate is the old baseline on8765, not the held card.
