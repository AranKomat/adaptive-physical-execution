# Contact observability and instruction-contract audit

## Findings

This is an evaluator-side static source audit, not an input to the motion planner.
No commands, reset, geometry changes or new model calls were made for this audit.

The upstream scene describes the PC mesh as visual-only and its collision as an
invisible fixture (channel, floor, end stops, board plate and rear I/O panel).
It explicitly describes a straight vertical drop as blocked by the panel before
the bracket passes through its cutout. Source:
`upstream/EmbodiedSWE/robobench/suites/assembly/scenes/pc_gpu_assembly.py:1`.
This is a plausible alternative explanation for the failed straight-down contact,
not proof of which bodies collided in that trial. It also means that a rendered
socket surface is not sufficient evidence of the collision channel's shape.
The audit does NOT establish that every relevant obstacle is visually absent or
that completion with legal observations is impossible.

There is also an instruction mismatch. Upstream `describe()` (same file, line337)
gives a qualitative bracket-through-cutout sequence before slot alignment and
pressing. Our `configs/tasks/pc_gpu_grasp_wrist_aim.json` instead says:
"Install the loose graphics card into the computer case's PCIe slot. Use visual
feedback to align and seat it." The backend passes that configured instruction,
not `describe()`, into the observation (`backends/embodiedswe.py:114`). Thus this
trial is not instruction-matched to the upstream task framing. This does not
prove that richer instructions alone would solve the physical task.

The grader defines equal grasp/alignment/press rungs; the grasp milestone is
latched (`upstream/EmbodiedSWE/robobench/suites/assembly/grader/pc_gpu_assembly.py`).
The recorded 0.33333334 is grasp-milestone credit, not partial insertion or even
proof of current retention. Retention was assessed separately from images.

## Evidence already obtained

- Failed contact: 26.291 mm / 0.176089 rad endpoint error, visibly tilted card.
- Posthoc evaluator: success=false; score 0.33333334, excluded from recovery input.
- Image/robot-state/receipt-based Astra withdrawal: 5 cm, 64 actions, 1.600 mm
  final error. Retained but tilted; not full recovery or installation.
- Current recorded state: episode d3645c724ce046aeab7dbd48580af359, observation1800.
- New contact tracking guard has CPU tests only and is not loaded in that worker.

## Next experiment boundary

1. Preserve the recovered episode; do not retry descent with the old worker.
2. Qualify the new tracking stop on an isolated worker before further contact.
3. Compare minimal instructions against a separately labeled instruction-assisted
   condition only after choosing that information contract. Use identical legal
   observations and controller limits; record the entire instruction difference.
   Do not call the instruction-assisted condition an unchanged minimal-input run.
4. Neither condition receives source-derived coordinates, seat tolerances,
   collision meshes, evaluator scores or hidden object transforms. Do not call
   `describe()` dynamically: its output includes configured-state assumptions.
5. Judge physical progress by observed interaction plus isolated posthoc native
   scoring, not a better verbal plan. A correct plan alone does not advance a phase.
6. If visible geometry remains insufficient, record the observation limitation;
   an observable-fixture variant is a different experiment, not a benchmark fix
   to be silently applied.

Avoid another same-view endpoint/prompt sweep or a hidden-geometry-informed
rearward command. The task remains nonprivileged adaptive assembly and recovery;
no phase is marked complete by this audit.
