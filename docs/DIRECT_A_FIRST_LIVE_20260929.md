# First live Direct-A qualification

## Outcome

The fresh three-decision run completed without errors. It validates a bounded
sensor -> Astra -> action -> receipt/history -> Astra loop, not task competence.

| Item | Result |
|---|---|
| Model | `openai/gpt-6-astra` |
| Route | OpenRouter Chat Completions; `openai/flex` only; fallback disabled |
| Requested service tier / reasoning | Flex / medium |
| Mode | `direct_roboicl` |
| Native scene | `assembly.pc_gpu.franka.joint`, seed 0, grasp weld enabled |
| Decisions / executed control steps | 3 / 12 |
| Simulated time / episode wall time | 0.8 s / 37.77 s |
| Total model-call latency | 17.26 s |
| Reported API cost | $0.056936 |
| Tokens | 10,987 input; 710 output (151 reasoning); 5,042 cached input |
| Action rejections / runtime errors | 0 / 0 |
| Native success / score | false / 0 |
| Termination | Decision budget reached |

Measured hand height fell from 0.55347 m to 0.37809 m (17.54 cm). The model
requested an open-gripper downward approach; later decisions referred to measured
progress and tracking lag. Final RGB still shows an open gripper above and offset
from the upright card. No grasp, insertion, or task success was demonstrated.

## Integration failures retained

1. The first Responses-route request received HTTP 404: OpenRouter found no route
   supporting the requested parameter combination. No model result or action.
   Its $1 shared-ledger reservation remains held; this is not counted as free.
2. An explicit Chat adapter then produced one valid decision and three control
   steps, costing $0.01438. Decision two failed locally because stored function
   calls/receipts had not been converted into Chat history. No second API call.
3. History conversion was fixed and regression-tested before the fresh completed
   three-decision trial. No automatic retries, model fallback, or guard relaxation.

Total reported cost for successful API responses in this sequence: $0.071316,
plus the unresolved $1 reservation. The existing $75 shared ceiling and other
holds remain intact. Credentials stayed on the Mac, with a loopback SSH tunnel
to the simulator. Public source contains neither credentials nor account ledger.

The suite now has 97 passing CPU tests. They cover explicit provider pinning,
Flex selection, image/schema conversion, tool-call/receipt history pairing, and
rejection of incomplete/non-tool output. Wire protocol selection is explicit in
the endpoint URL, not a runtime fallback.

## FLUX status

Upstream `predict_action_chunk` returns absolute commands in dataset units and
does not clamp gripper predictions. The retained proposal's minimum closed
fraction (-0.00446) is therefore not a missing adapter unit conversion.
All joint increments in that proposal are below 0.15 rad (maximum 0.04565 rad).
This does not qualify the full proposal: gripper validity, FK/path checks, and
task-transfer behavior remain open. No FLUX actions were executed.

## Artifacts and next experiment

Local ignored run: `runs/astra_flex_direct_a_history_20260929/`, including a report,
four observation boundaries, RGB frames, execution receipts, and verified trace.
Full per-control-step sensor recordings are backed up locally under
`runs/astra_direct_history_recordings/`. API requests/responses remain in the
adjacent `_api` directory and are not published.

Trace SHA-256: `bd63e7f2dc300ff6a2fe5552762be92efa1418d533fe289828d9825abd425554`.

Next: a longer, fresh bounded Direct-A run to test alignment and actual grasping.
Keep Hybrid gated until gripper handling is explicitly resolved and the full
proposal passes qualification. Keep perception, assistance settings, seeds, and
camera placements declared when comparing modes.
