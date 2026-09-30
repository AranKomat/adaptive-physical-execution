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

## Authorized baseline retirement and failed Isaac startup

User selected backup/retirement of8765, preserving8772. Fresh baseline observation
was `3cff69ee0d184428a33eb0af51fd1937:280`. Full recording tree copied to local
`runs/baseline8765_full_backup_20260930`:2531regular files,916199598bytes.
Checksum-only rsync then exited0 with no itemized differences. Terminal public
observation/images copied to `runs/retire_baseline8765_observe_20260930`.
Remote recording files remain untouched.

After verifying its exact command, sent SIGTERM to PID13434. Cleanup released
some memory but the same worker remained alive; finished its authorized retirement
with SIGKILL to that exact PID. Subsequent process inspection showed it absent
and held PID103000 present. GPU0 then had8203MiB free; GPU1 had1918MiB free.

The isolated compute library also passed a NEW PyTorch CUDA allocation and
synchronization (one scalar tensor). However, the separately launched1920x1080
Isaac worker on8780, PID336278, failed renderer initialization:

- NVML mismatch inside Kit (`return code18`).
- Vulkan `ERROR_INCOMPATIBLE_DRIVER`; no GPU Foundation device.
- PhysX GPU pipeline unavailable, attempted software fallback.

Stopped only this newly failed worker immediately to prevent invalid CPU-mode
experimentation and unnecessary CPU load. PID336278 is confirmed absent;
held103000 remains present. No model call, reset request, control command,
qualified high-resolution capture or task phase completion resulted. Do not
interpret startup failure as a manipulation or resolution result.
Local log: `runs/gpu_sensor1920_startup_failure_20260930.log`.

No host reboot/system package installation occurred. Next infrastructure work
must qualify the full Isaac/Vulkan driver stack, not infer it from a PyTorch
check. A reboot would lose remaining live simulator states and could interrupt
the separate CPU workload; it must not happen silently. A process-local matching
graphics-library condition or a coordinated restart are distinct options.

## Full process-local graphics attempt

Downloaded148MB `libnvidia-gl-580=580.95.05-0ubuntu1` and extracted it into the
same isolated tree, without a system package installation. Selected a private
Vulkan ICD descriptor pointing directly at that tree's `libGLX_nvidia.so.0`.
The fresh launch also preloaded matching NVML and CUDA libraries, retaining
the same high-resolution config, GPU0, and four-thread OpenMP bound.

New PID337393/8780 had no NVML mismatch messages in its captured startup log,
but still reported Vulkan `ERROR_INCOMPATIBLE_DRIVER`, no GPU Foundation device,
and PhysX software fallback. Stopped that exact new worker; process inspection
confirmed it absent and held PID103000 present. No reset/control request or
qualified observation was produced. No model call or phase completion.
Local log: `runs/gpu_sensor1920_fullcompat_failure_20260930.log`.

This is a failed startup after a changed dependency condition, not a retry of
an ambiguous physical command. No further speculative loader/startup sweep is
planned. Confirm whether the unrelated CPU workload still runs before selecting
a coordinated driver repair/reboot, or move new experiments to a coherent fresh
instance. Existing host, live states, global driver configuration and CPU
workload were not rebooted or modified. Keep the original task goal open.

## Earlier host decision (superseded)

User reported the CPU workload still active, then delegated the choice under
uncertainty. Decision: preserve this host and all remaining live scenes rather
than reboot or modify global graphics libraries. Use a fresh1x4090 environment
for the immediate sensing/local-IK trial; simultaneous FLUX+simulator capacity
must be qualified separately. The prior single-GPU endpoint184.148.224.206:42477
returned connection refused. No Vast provisioning connector or CLI is available
in this session. Fresh SSH details are requested; the experiment goal is not
complete. Do not loop more loader attempts while awaiting a coherent GPU host.

## Existing-host recovery after user direction

User subsequently requested continued work on the existing 2x4090 host. A
standalone Vulkan probe identified the missing matching dependency:
`libnvidia-gpucomp.so.580.95.05`. Extracting the vendor gpucomp package into the
private compatibility tree fixed Vulkan instance creation (return code 0).
No reboot, global package installation or driver change occurred.

New worker PID338829 on8780 initialized GPU0 rendering using matching process-local
CUDA/NVML/GL/gpucomp libraries and a private Vulkan ICD. Native legal captures
contain three1920x1080 PNGs and matching depth arrays. Startup still emitted
CUDA-state/NVML-handle warnings; this is not a claim of a warning-free stack.
No Vulkan fatal error or PhysX software fallback was found in this launch.
GPU0 had962MiB free and GPU1 had1918MiB free: do not add another worker.
Held PID103000/8772 and the unrelated CPU workload remain preserved.

Fresh Astra selected right[1095,771]. The original fixed2px refinement rejected
the edge. Measured top-plane pixels exist just beyond that radius. The planner
now preserves the2px-at640 same-FOV search footprint (maximum6px at1920), retaining
the3x3 measured patch,10mm depth-spread,45deg normal and1mm RMS requirements.
It selected[1096,769], upward cosine0.998935 and RMS3.06e-8m. This is sensor
refinement, not privileged object localization or clearance certification.
An operator-defined open-hand standoff sequence was submitted on8780, with no
closure authorized. Results are recorded separately from startup qualification.
Full CPU suite:392 passed. New task completion is not established by these checks.

The bounded approach completed seven local stages/235 actions and paused at
`28eee6eaefa546529c9118f2aff58e25:235`. Final hand tracking error0.0645mm and
rotation error0.000894rad met strict standoff arrival. No descent, closure, lift,
insertion or release was executed. This is endpoint tracking evidence only.
Stage wall times total about350.2s for15.67s of simulation. Local receipts and
review images: `runs/gpu1920_standoff_20260930`; final legal RGB-D:
`runs/gpu1920_standoff_flat_20260930`. Existing held8772 remains preserved.
Focused new-file lint passes; planner lint still has its pre-existing executable
bit and dict-constructor style findings. All392 CPU tests passed.
