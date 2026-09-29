# GraspGen-X displaced-card proposal test

## Result

One seed-0 batch of32 diffusion proposals returned the top8 in0.688seconds,
excluding installation and model loading. No robot action or paid model call.
Scores0.925--0.968 are learned ranking scores, not calibrated grasp success.
All8 hand origins are below the unchanged120mm pilot floor (about61--71mm).
Three endpoint IK solves converged from current robot joints. **None is admitted
for execution; regrasp and assembly remain incomplete.** Do not spend more
batches trying to solve this workspace restriction.

## Input and Frames

- Historical2195 wrist RGB-D:4096 sampled points from the operator-selected
  connected planar PCB surface. This is not a complete GPU or cooler cloud.
- At current2813, three visible sample projections agree within0.45mm; the
  remaining checks are occluded/outside the image. Entire-object stasis is an
  explicit assumption, not proven by those three matches.
- Coordinates are world meters. No object state, evaluator or hidden collision
  mesh was supplied to the model.
- Official Panda sweep-volume conditioning uses80mm open width and103.4mm
  nominal fingertip depth. Placeholder meshes are not used as collision geometry.
- The asset URDF rotates `panda_hand` by+1.5708rad about canonical z. Saved
  proposals include both `world_from_canonical` and `world_from_panda_hand`.
  Converting by the fixed right-multiplied transform is necessary; directly
  treating a canonical pose as a hand pose would rotate the closing axis wrongly.

## Provenance

Source: `NVlabs/GraspGenX`, revision
`b9429097728cb1c430dd78b92edf17ba318aad03`.
Weights: `adithyamurali/GraspGenXModel`, revision
`7c834043c11a11417e31d6d5ea9355801e40a2c1`; generator736/discriminator1056.
All four config/checkpoint SHA-256 hashes were checked before loading. Upstream
loads both model state dictionaries strictly; no missing-key fallback was used.
Gripper assets: `adithyamurali/gripper_descriptions`, revision
`19a03c00d19aeaf052d0f6801f0041982d676e8a`, `franka_panda/config.json` and
`gripper.urdf`, both checksum-verified. Franka asset attribution is Apache-2.0.

Isolated host environment: `/workspace/graspgenx-source/.venv`, Python3.11,
PyTorch2.6.0+cu124, NumPy1.26.4. Base inference dependencies only; optional
TensorRT metadata resolution was interrupted and replaced by `uv pip install`.
Transferred source ownership was corrected after a Git ownership build error;
no global Git safety exception, system package or existing environment changed.

## Runtime and Evidence

Both GPUs were initially nearly full. Idle FLUX PID16972 had no established
connections and was temporarily stopped after capturing its existing launch
configuration in process memory. All simulator processes remained untouched.
After the proposal process exited, FLUX was restored as PID75277 and its
authenticated metadata endpoint answered. Live episode was rechecked: still
`9fbd76d8e57641c79983eed82adbc2bc:2813`.

Model-reported peak allocated/reserved memory:593.3/656MiB. This excludes some
driver overhead and does not establish safe concurrent residency with FLUX.

Script: `scripts/probe_graspgenx_recovery.py`. Public retained
[input manifest](evidence/graspgenx_recovery_2813/manifest.json),
[partial cloud](evidence/graspgenx_recovery_2813/points_world.npy),
[receipt](evidence/graspgenx_recovery_2813/receipt.json),
[proposals](evidence/graspgenx_recovery_2813/proposals.npz), and
[robot screen](evidence/graspgenx_recovery_2813/robot_screen.json).
Three frame-contract tests added;243tests pass. These are not task-phase success.

Next: assess whether a separately qualified lower-hand workspace is appropriate,
using robot geometry and legal scene sensing, while preserving the held episode.
Do not bypass the live floor, treat planar-cloud scores as opposing-contact
evidence, or replay the failed inclined standoff. Collision/access qualification
is still required even if the software workspace restriction changes.
