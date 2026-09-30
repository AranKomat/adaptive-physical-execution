# Research Handoff: Native Sensing, Contact Failure, Branch Closure

Date: September 30, 2026 (JST).
Repository: https://github.com/AranKomat/adaptive-physical-execution
Previous consolidated handoff: [grasp and alignment](RESEARCH_HANDOFF_GRASP_ALIGNMENT_20260930.md),
cutoff `81a8134`. This report covers subsequent sensing, guarded approach,
contact, withdrawal and instruction-assisted geometry work through branch closure.
Code/protocol checkpoint before this report: `dbe6835`, pushed to `main`.

## Bottom Line

Fresh native1920x1080 sensing supported an assisted grasp, lift, approximately
43.9cm elevated carry and two downward standoffs. One bounded downward contact
probe failed on tracking error; a reviewed withdrawal succeeded. Added qualitative
assembly instructions and one exterior view still did not establish the bracket
and chassis-cutout passage. The focused mating-geometry branch is CLOSED.

**No successful installation/release, task recovery or matched enhanced
Direct-A/Direct-B/FLUX comparison was achieved.** The contact probe was not a
complete integrated insertion attempt. No new full task phase is claimed.
The proposed12cm lift-to-expose was not executed and is cancelled, not pending.

## Conditions And Information Contract

- Franka Panda in upstream EmbodiedSWE PC GPU assembly; existing2x4090 host.
- GPT-6 Astra Flex, medium reasoning, reviewing sensor evidence at stage boundaries.
- Operator-defined local differential IK, not per-step GPT Direct or FLUX Hybrid.
- Native grasp assistance ON; retention is not an ordinary frictional-grasp result.
- Idealized independently movable inspection camera without a collision body.
- Legal RGB-D, calibration, robot FK/proprioception and receipts inform control.
  Historical evidence is labeled with observation provenance, not treated as current.
- Unknown external clearance remains exploratory. Per-action tracking guards monitor
  pose deviation, not contact force; visual monitoring is at returned stage boundaries.
- Hidden object transforms, source-derived fixture geometry and grader feedback are
  excluded from planner input. Evaluation occurs separately after the attempt.

## Results Since The Previous Handoff

| Experiment | Result | What It Does Not Establish |
| --- | --- | --- |
| Original held episode, focused keyed-placement views | Current gold/rim samples available, but final endpoint/key review declined correspondence | No insertion or proof that the task is impossible |
| Separate native1920 sensing and fresh grasp | Open descent reached331; closure reached459; short lift523 needed a separately bounded extension; extension reached667 with visibly retained card | Not autonomous, unassisted or original-camera success |
| Elevated carry to1059 |328actions; strict arrival0.877mm/0.000427rad; images show retained card | Not mating alignment |
|10cm standoff to1157 |98actions;1.958mm/0.0000805rad arrival | Not contact or seating |
|6cm near-standoff to1241 |84actions;1.223mm/0.000420rad arrival | Not verified channel clearance |
|61.132mm downward plane-contact hypothesis |42actions; stopped at1283 on10.174mm position error,0.024181rad attitude error | Not complete insertion; cause/body of contact unmeasured |
| Reviewed3cm upward withdrawal |64actions; reached1347 with0.824mm/0.002138rad strict arrival; card visibly retained | Not task recovery or installation |
| Static instruction-assisted review plus exterior camera hold | Review held at1347; camera64actions to1411; fresh review again held | No supported bracket passage, slide or release |

Posthoc native evaluation after withdrawal: `success=false`,
`score=0.3333333432674408`. This is latched grasp credit, not partial seating
or proof of current retention. The planner did not receive that score.

## What We Learned And Fixed

Native detail helped distinguish endpoints, but did not automatically solve
occlusion or hidden geometry. One earlier731 connector endpoint deprojected to
background table depth and was rejected. Correctly scoped paired crops at1059
then produced four qualified current endpoint samples; a too-tight crop initially
omitted the selected lower socket and was corrected without moving the robot.

Dark-gap samples at1157 had essentially rim-height depth rather than a measurable
recess. This is evidence about rendered sensor surfaces, not collision truth.
The evaluator-side source audit found a visual-only PC mesh and separate invisible
physical fixtures, plus a missing qualitative assembly sequence in our initial
instruction. This is a plausible explanation, not causal proof of the guard stop.

The instruction-assisted condition added bracket-through-cutout-before-seating
guidance, with no numerical source geometry. It still failed to establish passage
in the legal images. At1411, one sampled chassis rim was44.877mm above a sampled
PCB reference; those two points do not establish full-object clearance.

Software corrections included native-coordinate declarations in scene reviews,
current crops with explicit pixel mapping, historical target provenance in gap
reviews, and fresh affirmative review plus tracking guards for contact proposals.
The review prompt now has a validated explicit translation proposal bound; default
remains5cm. This is advisory only and does not relax execution gates. The12cm
option was prepared but no12cm physical move followed.

## Runtime And Resource Issues

The high-resolution launch initially failed from NVIDIA library/driver mismatch.
Matching process-local graphics libraries, private Vulkan ICD and matching
gpucomp resolved Isaac startup without reboot or global driver changes. Held
episodes and unrelated CPU workload were preserved. This was infrastructure
repair, not a robotics phase result.

Native1920 rendering remains expensive:10cm approach150.99s wall/6.53s simulated;
6cm approach127.03s/5.6s; contact62.68s/2.8s; withdrawal95.92s/4.27s.
These stages execute locally without per-control-step GPT calls. The simulator
wall-time multiplier remains a bottleneck; do not attribute all slow video to
model reasoning or prescribed physical velocity.

The two final instruction assessments cost$0.11904875 combined; the three preceding
contact/withdrawal assessments cost$0.1592575. These are scoped subsets, not total
campaign spend. Shared API ceiling remains$85 with unresolved holds intact;
last known reservation count4532. Verify the private ledger before any new call.
No paid call or robot motion was used to close this branch and write this report.

## Preserved State And Evidence

Current native worker8780: episode `28eee6eaefa546529c9118f2aff58e25`, observation1411,
confirmed by a fresh read-only capture during backup. Original worker8772 remains
protected; last captured `5fc1330e1fb9410e9cc56d5c948ee0af:1754`.
No worker was retired, reset, released or stopped by branch closure.

Remote repository: `/workspace/adaptive-physical-execution`.
Important local run artifacts live under `runs/gpu1920*`; they include selected
RGB-D/calibration captures, proposal messages, plans, model responses and receipts.
The closure archive also retains native stage/command logs and recording metadata.
Backup verification is recorded in `BRANCH_CLOSURE_BACKUP_20260930.json` next to
this report. Private run/API artifacts are not published to GitHub.

The38GB full native frame-by-frame recording remains remote; the archive is an
important subset, NOT a complete instance backup. Live physics state is not a
portable checkpoint and would be lost if the instance/worker is destroyed.

Public detailed evidence:
[native grasp/lift/carry](HIGH_RESOLUTION_GRASP_20260930.md),
[contact failure and withdrawal](NATIVE_CONTACT_NEGATIVE_20260930.md),
[observability audit](CONTACT_OBSERVABILITY_AUDIT_20260930.md).
Latest verification:428 CPU tests passed; targeted Ruff checks passed.
Tests do not complete physical phases.

## Next Sequence And Stopping Rule

1. Do not reopen nearby camera, aperture, endpoint or rail-prompt sweeps on this
   closed branch. Do not execute the cancelled12cm lift or retry downward seating.
2. If continuing GPU assembly, use the separately labeled
   [observable-fixture diagnostic protocol](VISIBLE_FIXTURE_DIAGNOSTIC_PLAN_20260930.md).
   Render existing physical surfaces without modifying physics/scoring, verify
   structural USD differences and actual RGB-D visibility, and exclude source
   coordinates from the planner. No variant asset/worker has yet been executed.
3. Once visible geometry supports it, attempt one integrated bracket passage,
   alignment and seating sequence with existing guards. Otherwise freeze that
   diagnostic too. Do not silently count changed rendering as original success.
4. Independently verify release/support and native success. Then test actual task
   recovery and matched enhanced Direct-A/Direct-B/FLUX trials with equal sensing,
   controller opportunities, assistance and budgets.
5. Execution-memory comparisons remain downstream of useful verified physical
   effects; answer-only studies and additional component tests are not substitutes.

The project remains promising for low-call-count sensor-guided local execution:
grasp/lift/carry are concrete, not merely verbal plans. The central unresolved
problem is reliable mating under the current observation/fixture contract.
We have not shown that another model, a physical robot, or a better visible fixture
would succeed; those require new evidence, not inference from this negative branch.
