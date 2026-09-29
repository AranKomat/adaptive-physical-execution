# Projected sensor memory and near standoff

Same held episode, revalidated at 1503. No reset. Project the historical
socket surface measured from legal RGB-D into current cameras, with labeled
static-surface assumption, frame/episode checks and actual depth residuals.
Depth consistency is not semantic identity, collision clearance or endpoints.

Fresh correspondence review now identifies the original lower silver-edged
socket instead of its neighbor. Right projected anchor [320,316] matches depth;
left is inconsistent/occluded and wrist is outside frame. Review still says
inspect: connector ends and socket opposite-from-bracket end are visible, but
socket bracket-side end and key are unresolved.

All three selected surfaces pass unchanged 3x3/10mm depth checks:
- Connector bracket end [280,208]: [0.43383009,0.02779858,0.16231393].
- Connector opposite end [382,230]: [0.52908829,0.02743902,0.16068232].
- Socket opposite end [374,327]: [0.52774101,0.03072447,0.03785896].

Corresponding visible-end horizontal difference is 1.347 mm in x / 3.285 mm
in y. Vertical difference 122.823 mm. Full endpoint correspondence and gap
centerline remain unknown; these approximate surface samples are not exact
mechanical mating references.

## Predeclared near approach

One simulator-only operator-scoped vertical approach: at most 6 cm down,
at most two local chunks/128 actions, unchanged grip and attitude, no lateral
correction, nominal remaining feature gap >=6 cm. New explicit near mode requires
two accepted connector samples, at least one accepted socket sample and a labeled
matching end within 10 mm horizontally. It does not convert the model's inspect
decision into insertion approval. Unknown whole-card/bracket swept clearance
is explicit; no contact intended, no insertion/release, no automatic retry.
Strict controller endpoint checks and hard stops remain unchanged. Fresh review
is required afterward. The prior coarse approach default remains 12 cm nominal
standoff. Neither mode is a real-hardware safety controller.

Near approach completed at 1587: 84 actions / 5.6 sim seconds / 39.523 execution
seconds, final 1.213 mm / 0.000384 rad. Fresh review still says inspect. It tracks
the original socket via projection, but reverses connector bracket-side labels
relative to the prior same-camera review despite no commanded rotation. Do not
use this inconsistent semantic end assignment for insertion. Earlier same-side
surface alignment supported only the explicitly exploratory standoff approach.

Next predeclared camera-only inspection: eye [0.472,-0.14,0.31], gaze
[0.47224,0.02803,0.038], 64 holds, unchanged arm/grip. This approaches the socket
from the exposed PCB side and centers the historical socket region, rather than
looking at the whole card. Translation/angular preflight passes unchanged limits.
Unknown camera clearance remains explicit; no further descent or release.

## Outcome at 1651

Camera move passed: 64 actions / 30.417 wall seconds, arm error0.739mm /
0.001632rad. Eye[0.472,-0.14,0.31], gaze[0.47224,0.02803,0.038]. Close image
exposes the card's gold strip and large reinforced socket. Fresh review retains
socket identity but declines all exact endpoints/key; bracket-side association
and contact-bank versus retention-tab distinction remain unresolved. No insertion
or release. Current held episode d3645c724ce046aeab7dbd48580af359:1651.

Read-only legal-depth diagnostic: at right-image columns280,300,320,340,360,
rows172..184, deprojected world z is approximately0.0375918..0.0375939m in every
column, only about2micrometers variation. These radius-zero diagnostic samples
are NOT gate-qualified motion samples. The apparently dark channel region is
nearly flat in this capture; it does not resolve an opening along these profiles.
This does not prove that the whole asset lacks a slot or that another view could
not resolve geometry. It limits what can be inferred from the current sensor
image: do not claim measured insertion-gap/key geometry from this flat surface.

Next avoid another exact-endpoint prompt/camera sweep. Prepare an explicitly
exploratory bounded contact hypothesis based on visible surfaces and robot
feedback, separating approximate mating assumptions from observed evidence.
Fresh held-feature depth/retention and current command bounds must be checked
before contact. No such contact command has yet been issued; do not treat this
note as a verified insertion plan. Keep privileged scoring outside control.

Three new calls cost$0.141445; episode cumulative$0.40187125. Reserved calls4369;
recheck private ledger before more calls and retain unresolved holds. 214 tests
pass. Public evidence includes projected/near/close correspondence reviews,
endpoint measurements, near-standoff image/receipt and close socket image under
the aimed-lift evidence directory. Selected RGB-D/logs local, complete recordings
remote. Existing video still ends1213. Full installation/release/recovery remains
unachieved; no phase completion is inferred from these component tests.
