# Higher-resolution sensing: prepared, not physically tested

The same-view correspondence branch ended at held episode1754 after full-frame
and explicitly mapped crop reviews both declined endpoint/key association.
Do not repeat that branch or convert the decline into proof of impossibility.

Inspection found that simulator camera size is configurable, but targeting
prompts assumed640x360. The request builder now reads actual image dimensions,
rejects inconsistent camera sizes, and labels bounded overviews and crops with
original-sensor coordinate mappings. Returned pixels remain in the native frame
for deprojection against its unresized depth/calibration. Crops are nearest-
neighbor; no generated detail. API overview/crop images stay <=640pixels per
dimension, consistent with the current private request-reservation assumptions.

`configs/tasks/pc_gpu_sensor_1920.json` is an explicit1920x1080 condition. A
structured comparison against `pc_gpu_enhanced.json` found that only image_size
differs among nonmetadata fields. Camera placement, timestep, limits, physics
preset, and wrist aim stay unchanged. No FLUX or motion qualification is implied.

## Bounded experiment

1. Preserve the held8772 scene and its recorded evidence. Do not reset it to
   apply a new camera size. Verify available resources before a separate worker;
   do not kill another worker or interfere with the unrelated CPU workload.
2. Start a separately labeled fresh same-task/seed resolution condition only
   after deciding to continue this branch. Sensor resolution is static at worker
   creation in this adapter. Cached world targets are not fresh control evidence.
3. Check native RGB/depth shapes and current intrinsics, then reproduce the
   assisted recipe using fresh sensor targets. Keep operator assistance and
   native weld assistance disclosed. This is not a zero-shot matched-policy run.
4. Use a genuinely higher-resolution sensor crop of the mating region, plus
   bounded full-scene overviews. Example targeting command, with crop bounds
   selected from the NEW observation rather than blindly copied:

```bash
python scripts/prepare_sensor_target_request.py \
  --capture runs/NEW_NATIVE_CAPTURE --stage correspondence \
  --closeup-right X0 Y0 X1 Y1 --output runs/NEW_REQUEST.json
```

5. If usable task-relative geometry is recovered, compile and review one integrated
   bounded approach/contact attempt with abort/recovery and separate physical
   verification. If not, record the specific missing evidence and end this
   resolution branch, rather than sweeping wording, viewpoints, or crop bounds.

No new GPU worker, motion, model call, installation or completed phase is claimed
by this preparation. Existing held state is unaffected. Historical context
images and other review builders are not automatically higher-resolution aware;
this preparation covers current targeting requests, not every planner path.

Verification:385CPU tests passed. Tests cover original-coordinate prompt text,
bounded image sizes, crop mapping, mismatched-size rejection, and existing
targeting/history behavior. Former placeholder image bytes in prompt tests were
replaced by valid PNG fixtures because the builder now validates image dimensions.
These tests do not establish that higher resolution resolves the physical task.

## Execution update

The existing host now runs a qualified native1920x1080 capture worker on8780,
using process-local matching Vulkan dependencies (see capacity report). The
original held8772 episode remains unchanged. One fresh Astra Flex medium target
call cost$0.0359025. Its edge pixel failed the fixed2px search; resizing the
bounded search to6px recovered a measured upward plane without loosening the
spread/normal/RMS checks. An open-hand standoff trial is underway, with an
explicit pause before descent/closure. This is fresh image/depth targeting plus
an operator-defined recipe, not FLUX or an autonomous grasp planner.

Native-resolution rendering and recording are expensive:39 actions represented
2.6 simulated seconds but58.2 wall seconds;117 actions generated3.4GB of sensor
recordings. Keep this branch bounded. Future throughput work should distinguish
native decision-boundary captures from every-step recording; do not sacrifice
fresh monitoring or silently change comparison conditions.392 CPU tests pass.

Approach outcome: seven stages/235 actions reached standoff and paused before
descent at sequence235. Final position error0.0645mm; rotation0.000894rad.
About350.2s wall time versus15.67s simulated time. No grasp/contact or assembly
success follows from endpoint arrival. Preserve the final native RGB-D for the
next close-range geometry decision rather than reuse the initial target blindly.
