# Oblique pre-closure inspection

Episode `92a08cc3751a4fd29a2025d079d2860e`. Fresh sensor-target/local-DiffIK
trial, no FLUX or Hybrid replay. Changed only external-right placement through
`configs/tasks/pc_gpu_grasp_oblique.json`: eye [0.55,-0.65,0.4], target
[0.22,-0.34,0.2], focal 18. Overview/wrist, 15 Hz control and physics unchanged.
Camera target chosen from retained legal RGB-D and robot geometry; no hidden
object state supplied. This static idealized view is not a physical camera rig
or a demonstrated active-perception policy. Grasp assistance remains enabled.

## Observed result

- Initial view showed the card's top at larger scale, with the bottom cropped.
- Fresh Astra selected right pixel [364,258], measured depth 0.506809 m,
  3x3 spread 2.626 mm, no refinement. This remains a surface point, not a grasp.
- Operator-defined open-gripper approach: ten stages / 640 actions / 42.667
  simulated seconds / 277.615 execution wall seconds. All endpoint checks passed;
  max position error 2.013 mm, final error 1.187 mm.
- `--pause-before-close` stopped at observation 640; no closure or lift executed.
- Fresh pre-closure review returned `inspect`. Rough longitudinal centering was
  supported and straddling plausible, but the far inner pad was obscured by the
  hand and near-finger/support separation unresolved. No definite collision or
  directional correction was inferred. Suggested view: oblique end-on, exposing
  pad-to-face gaps and the support edge.
- Two Astra Flex medium calls, $0.06194875 total. No task or grasp success.

An initial config ID was rejected before simulator initialization; fixed to keep
the existing pc_gpu task ID. No actions/API calls occurred in that startup.
167 CPU tests pass; the new config also passes the actual task loader.

## Consequences

Better framing improved centering evidence but did not remove hand occlusion.
Do not label this grasp failure: grasping was not attempted. Conversely, do not
count a paused arm or reviewer caution as a completed manipulation phase.

Stop repeating full approaches to try nearby static cameras. Next work should
enable a bounded end-on observation at a held pose, or combine calibrated robot
pad geometry with measured local surface geometry, preserving visibility and
uncertainty limits. Merely demanding that RGB show every contact may itself be
too restrictive; test a robot-geometry-assisted decision rather than assume
physical impossibility. Do not relax the stated no-close-on-inspect rule after
seeing this result. Model-authored execution/recovery and full assembly remain
the goal, not more operator-defined endpoint demonstrations.

Evidence: `docs/evidence/grasp_oblique_20260930`; full local recordings and API
audits under `runs/grasp_oblique_20260930*`.
