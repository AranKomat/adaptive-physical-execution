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

## Observed-surface screen: do not lower the floor to admit these proposals

The follow-up screen changes the next action: the software floor is not the
only obstacle. A nominal public Panda collision proxy at these poses extends
32--43mm below world z=0. Four legal tabletop depth samples lie at z=0.55--0.82mm.
Continuing that plane under the occluded case is an assumption, not observed
occupied volume at the grasp. Nevertheless, these poses are not justified by
simply reducing the hand-origin limit.

| Candidate | Contact surface hits | Raised-standoff hits | Minimum proxy z (mm) |
| --- | ---: | ---: | ---: |
| 0 | 139 | 244 | -36.4 |
| 1 | 84 | 63 | -33.2 |
| 2 | 75 | 55 | -32.5 |
| 3 | 0 | 701 | -36.9 |
| 4 | 1 | 0 | -42.5 |
| 5 | 3 | 1 | -35.9 |
| 6 | 0 | 1341 | -36.3 |
| 7 | 0 | 4245 | -37.0 |

Hits are measured current RGB-D points more than2mm inside the union of proxy
components, sampled every second pixel. They are NOT collision probabilities
or independent measurements. The raised standoff translates each pose60mm up.
No arm or swept path was screened. Current robot points and intended contact
surfaces are not excluded; zero hits never establishes free space.

`scripts/screen_graspgenx_observed_surfaces.py` checks the pinned nominal mesh
hash and attached depth calibration, and records representative pixels for
review. The mesh is from the same pinned gripper dataset above, SHA-256
`6feba508f92c6c6609d6639c4c2883200aaacd31f507370d479b25be1ea0e3b8`.
It has nine watertight components; it is not a verified native simulator collider.
See [screen](evidence/graspgenx_recovery_2813/surface_screen.json) and
[table samples](evidence/graspgenx_recovery_2813/table_samples.json).

The initial rectangular input crop omitted visible PCB surface near some
proposed palms (current right-camera upper edge, x about0.387m). Removing the
historical crop indiscriminately is also invalid: the connected planar component
extends to y=-0.079m and x=0.625m, without verified object membership. The expanded
cloud is **rejected pending semantic review**, not an improved model input.
Coplanarity and connectedness do not establish object identity.

Next requires a materially different accessible grasp/contact strategy grounded
in the current scene, not another batch on the same partial plane. Preserve2813;
do not replay the failed inclined standoff or relax the workspace limit. No new
motion, model inference, or task-phase completion came from this offline screen.
