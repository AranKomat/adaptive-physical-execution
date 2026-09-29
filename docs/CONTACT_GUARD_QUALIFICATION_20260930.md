# Contact guard: native free-space qualification

An isolated worker loaded the new guard from a separate source copy, on port8768.
The held-card worker8767 was not reset, hot-reloaded or commanded. No paid calls.
Same task configuration and native DiffIK with rotation-integral feedback;
fresh seed0 episode1847da134b594076ae3cee201009d6f6, open gripper.

Run `scripts/probe_local_stage_service.py --contact-tracking-guard` against the
isolated worker. This option checks advertised capability before reset and sets
the guard on both requests. Targets use only the measured robot hand pose.

| Stage | Actions | Sim seconds | Execution seconds | Final position error |
| --- | ---: | ---: | ---: | ---: |
| Hold | 30 | 2.0 | 12.823 | 0 mm |
| Upward 1 cm | 60 | 4.0 | 25.461 | 0.247 mm |

Both returned `local stage arrived`. Final rotation error0.00007783rad.
This establishes guard-enabled native normal-path execution, NOT a native
contact-stop test. The threshold-crossing stop branch still has only the
controlled fake-stall regression test. No claim of physical force limitation,
collision clearance, grasping, insertion or phase completion follows.

Temporary PID60710 was closed with SIGINT after the client completed. Raw
recordings and requests/receipts are backed up under
`runs/contact_guard_qualification_20260930/`. Original simulator and FLUX were
not changed. The old held-card worker still does not contain the guard.

Next: an integrated, separately labeled assembly trial on updated code, with
fresh sensor grounding, bounded contact and one reviewed recovery if needed.
Do not repeat free-space checks as a substitute for manipulation progress.
The instruction-contract distinction remains documented in
`CONTACT_OBSERVABILITY_AUDIT_20260930.md`. Software regression suite:217passed.
