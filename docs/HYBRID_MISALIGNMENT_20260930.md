# Hybrid reviewer catches premature grasp intent

Run `hybrid_recovery_20260930`, episode `cdbf09a5af93410795f6562dbcc0e65c`.
Same original cameras, FLUX native gripper conversion, Astra Flex medium, nominal
robot pinch-center context. The fixed two-uncertain-chunk stop rule was removed;
action validators and eight-review/256-action budget remained unchanged.

The reviewer accepted six FLUX prefixes (16,16,12,8,12,12), totaling 76 actions.
On review seven it marked the next intent `misaligned`: the fingers remained
above/beside the card, while FLUX proposed narrowing followed by raising/retreating.
It stopped rather than executing that proposal. Final image still shows the card
on its support. No grasp, lift, corrective action, recovery, or task success.

- 5.067 simulated seconds, 106.694 wall seconds.
- Seven calls, $0.76792875; reported model latency 42.047 s.
- Zero software rejections, no runtime error; native success=false.
- All 76 executed actions were unedited FLUX proposals. Misalignment detection
  is not evidence of successful correction or a collision-safety certificate.

This resolves the question of whether the two-chunk cutoff alone prevented the
reviewer from seeing a grasp failure: without it, the trial reached a concrete
premature-closure concern. It does NOT isolate the effect of pinch context or rank
the policy; proposals and reviews are stochastic and prior budgets differ.

## Branch decision

Stop repeating free-running FLUX approach trials with only prompt changes. Current
evidence supports approach motion and detection of a bad grasp proposal, not
adequate grasp geometry or task competence. Next supply a legal RGB-D-derived
target and robot pad geometry to a bounded correction stage, then test an actual
grasp/recovery. Disclose target selection, any operator-defined execution recipe,
and whether correction is model-selected; do not relabel the previously successful
scripted sensor lift as autonomous Hybrid recovery.

The sensor-target local controller already achieved assisted lift/carry, while
precision insertion remains unresolved. Reuse that measured capability rather
than conducting another controller or checkpoint sweep. Do not use hidden target
coordinates or native grader flags to guide correction.

Evidence: `docs/evidence/hybrid_recovery_20260930`; complete raw recordings are
backed up locally. Only this temporary simulator is stopped after backup.
