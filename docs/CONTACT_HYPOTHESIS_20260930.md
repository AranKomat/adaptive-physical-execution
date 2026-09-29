# Bounded sensor-surface contact hypothesis

Same held episode revalidated at 1651; no reset. The close-up depth does not
resolve an insertion channel/key, and exact endpoint correspondence is uncertain.
Do not call this a certified insertion or an autonomous GPT decision.

Operator selects visible contact-strip interior pixels [310,116],[380,118] and
the depth-consistent historical socket anchor [320,180] in current right image.
All pass the unchanged 3x3/10mm depth test. Contact strip surface heights are
0.0989978 and0.0976329m; socket surface0.0375924m. The minimum vertical gap is
0.0600405m. No privileged object pose or hidden collision state used.

## Predeclared experiment

Explicit simulator-only contact hypothesis: translate down by that measured
minimum gap, no lateral/attitude/grip change, no commanded extra push below the
observed plane. At most8cm descent and two local chunks/128actions; nearest
feature samples must be within25mm horizontally. Existing raw stop/arrival
checks remain. Whole-card/bracket swept clearance, mating geometry and force
are unknown. The controller is not force-limited or real-hardware qualified.
No automatic release, retry or follow-on descent. Record actual outcome, then
review images and read evaluator-only scores afterward, outside motion planning.
Grasp assistance remains ON; operator-defined recipe remains disclosed.

## Contact result and recovery decision

First chunk passed at1672. Final chunk ended at1736 without arrival: position
error26.291mm / rotation0.176089rad (~10.09deg), versus prior free-space1-2mm.
85actions /5.667sim seconds /40.165execution seconds. Card visibly tilted near
the socket. No extra push/retry/release. Native evaluator read only AFTER the
terminal contact result: success=false, score0.33333334. This partial score
is not seating evidence and was not supplied to the recovery planner.

Fresh Astra recovery request included actual images, robot-only state and the
confirmed nonarrival receipt. It selected lift_5cm, noting visible retention,
no clear entanglement and remaining hidden-clearance uncertainty. Execute one
64-action vertical5cm withdrawal with CURRENT measured attitude and prior grip
unchanged. No lateral correction, rotation restoration, release or insertion
retry. This is a distinct bounded withdrawal, not a retry of the failed descent.

## Recovery outcome and controller fix

Withdrawal completed at1800:64actions/4.267sim seconds/30.032execution seconds,
strict endpoint error1.600mm/0.002464rad. Current image shows the card elevated
and retained. It remains tilted because the recovery explicitly preserved the
measured attitude; original mating orientation was not restored. This is one
successful bounded model-selected withdrawal after an operator-defined failed
contact test, not autonomous full-task recovery or seating.

The contact error was not purely vertical: target-minus-actual translation was
[-17.519,-16.618,-10.398]mm, with rotation error vector
[0.03720,-0.06124,0.16085]rad. Contact/misalignment is plausible but exact contact
identity and force are not established. Do not simply push farther along z.

Added a contact-only per-action tracking guard: stop if actual hand departs from
the current ramp waypoint by >10mm or >0.10rad. Confirmed guard stops return a
distinct receipt, clear transit context and permit a separately reviewed recovery;
ambiguous native failures still poison the worker. Camera/contact commands cannot
be combined. Ordinary transit behavior stays unchanged. The contact runner now
requires advertised guard support before executing, so it refuses contact on the
old current worker. Software fake-stall test stops on action7 rather than running
the full64-action budget. 217 tests pass. THIS GUARD IS NOT LOADED/LIVE-QUALIFIED
in the current process; do not claim it governed the contact test above.

Current state d3645c724ce046aeab7dbd48580af359:1800, held/paused. Same worker54862
and tunnel14040. Eye[0.472,-0.14,0.31], gaze[0.47224,0.02803,0.038]. Selected
latest RGB-D/logs and recovery images/receipts are local; full recordings remote.
Public evidence in aimed-lift directory includes contact image/receipt, separately
labeled evaluator result, operator pixel selection and model recovery decision,
withdrawal image/receipt. Existing video still ends1213.

One recovery call cost$0.01484625; episode cumulative$0.41671750, reserved calls4370.
No further insertion/release. Next re-establish alignment/contact geometry from
the recovered tilted state, and qualify the new guard before any further contact
test (requires an explicitly fresh worker, not hot reload). Avoid interpreting
the flat socket texture/depth or partial evaluator score as successful seating.
