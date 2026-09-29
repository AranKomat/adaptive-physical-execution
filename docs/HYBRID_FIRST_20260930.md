# First bounded FLUX Hybrid execution

Run `hybrid_first_20260930`, episode `e65fdd8d62f14388bdd19622c17673ee`.
The fresh simulator used the original `pc_gpu.json` camera layout, not the
independent-camera or high-magnification condition. No cached pixel selections
or hand-authored motion targets were used. RGB and robot state were policy inputs;
recorded depth and native scoring remained outside the policy context.

FLUX DROID `gd-fp8r` proposed absolute joints, with explicit native joint-position
gripper clamping and unchanged joint targets. Robot-only FK previews went to
Astra Flex medium. Astra accepted three 8-action prefixes. All 24 actions executed,
zero rejections/errors, then the declared three-decision budget ended the run.
No task success, grasp, lift, insertion, or recovery was demonstrated.

- Simulated duration: 1.6 s; wall duration: 40.485 s.
- Three API calls: $0.2037775 from the settled ledger; reported model latency
  totaled 11.458 s. The run's generic cost field is null, not zero.
- Initial hand XYZ: [0.140079,-0.339979,0.553468] m.
- Final hand XYZ: [0.093152,-0.372155,0.511314] m.
- Chunk-end tracking errors: 8.82, 19.36, 9.15 mm; rotation 0.0412-0.0428 rad.
- Native score 0, success false. Final image still shows card on its support.

This establishes the first live proposal -> review -> joint-execution loop, not
FLUX competence on PC assembly. The duration is too short to rank it against the
longer Direct or operator-recipe trials. DROID camera/domain transfer and the
15 Hz declared simulator action rate remain experimental.

## Reviewer limitation and next test

The reviewer labeled descending hand motion as progressing/aligned without a
measured decrease in hand-to-target error. Treat that as its assessment, not an
independent progress result. Next use a bounded longer policy interval, explicit
visual target-relative progress assessment, and a stop on repeated no progress;
do not spend many short calls merely confirming that the arm moved. No clearance
certificate or precise insertion target has been established.

Evidence is in `docs/evidence/hybrid_first_20260930`; full local run contains
observations and all frame references used by the trace. Raw simulator captures
were copied locally to `runs/hybrid_first_20260930_recordings`. Only this trial's
temporary simulator was terminated afterward; existing simulator/FLUX services
and the rental were left untouched. Grasp assistance remains enabled.
