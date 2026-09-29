# Longer-prefix Hybrid attempt and command-domain ambiguity

Run `hybrid_longer_20260930`, episode `181b926208834023a2cfe26d987c0549`.
Original camera layout and FLUX native gripper conversion, as in the first trial.
Configured cap: five reviews, horizon 32, 160 actions. The reviewer was additionally
instructed not to equate hand movement with target-relative task progress.
Thus this is not an isolated horizon ablation.

Actual result: Astra accepted 24 actions from the first proposal, then stopped
on the second decision. Only 1.6 simulated seconds ran, not the full intended
longer duration. Wall time 33.255 s, two calls $0.13129125, zero software rejections,
no runtime error, native success=false. No grasp or recovery was demonstrated.
Chunk-end tracking error was 16.63 mm / 0.0410 rad.

The reviewer correctly withheld a progress claim, but described the next FK
preview's first displacement as violating the 3 cm per-step limit. Recalculation
confirms that displacement was 39.729 mm. However, the software's 3 cm limit
applies to EEF commands; joint-absolute proposals use a 0.15 rad per-joint target
step limit. This was a MODEL stop under an ambiguous prompt, not a software
rejection or proof of unsafe contact. The model can still judge such motion
undesirable, but must distinguish that judgment from a validator rule.

Fixed the prompt to state both command domains explicitly. Neither validator
limit was relaxed, no action was interpolated/clipped, and the stopped episode
was not resumed automatically. Added a regression test for the prompt distinction.
The next trial should use the clarified prompt and the same declared bounded
longer-prefix condition. Do not conclude policy failure or success from this
short reviewer-stopped run. The existing perception/insertion limitation remains.

Evidence: `docs/evidence/hybrid_longer_20260930`. Full simulator recordings are
backed up locally. The temporary simulator is stopped after backup; original
simulator, FLUX worker, rental, and unrelated CPU work are not modified.
