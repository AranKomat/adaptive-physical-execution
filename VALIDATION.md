# Validation report

Build date: **2026-09-29**.

## Executed in this environment

| Check | Result |
|---|---|
| Editable core-package installation (`--no-deps --no-build-isolation`) | Passed |
| CPU pytest suite | **86 passed** |
| All three controller software fixtures | Passed |
| Actual localhost HTTP server/client fixture rollout | Passed as part of pytest |
| Exact upstream RoboICL memory-file Git blob verification | Passed |
| Geometry/FK/Jacobian/IK numerical tests | Passed |
| Mock model HTTP and incomplete/refused/invalid-action rejection tests | Passed |
| Privileged-evaluator sentinel exclusion from model context | Passed |
| Duplicate command / stale observation / ambiguous execution handling | Passed |
| Gripper convention conversion and FLUX tensor-schema tests | Passed |
| Native-interface test doubles for simulator adapter and reference reuse | Passed; not a real simulator |
| HTML/CSV reporting and event/frame/result integrity tests | Passed |
| Bootstrap and campaign plan-only CLI checks | Passed; no repository download or GPU job launched |
| Python syntax compilation | Passed |

## Fresh ZIP extraction check

The source ZIP was extracted into a new directory. Running against the extracted `src/`:

```text
pytest -q: 86 passed in 3.15s
python -m physical_exec smoke: all three CPU fixtures passed
python scripts/verify_release.py: 109 shipped files verified
```

These checks used the extracted source, not a simulated success on a robotics task.
The final archive was rebuilt after recording this validation; executable source was unchanged.

## What these results do not establish

No actual GPT/API request, FLUX inference, Isaac Sim rendering, contact dynamics,
GPU/RAM insertion, real-robot operation, or sim-to-real transfer has been tested.
Native-interface test doubles exercise Python plumbing only. CPU fixture success is
explicitly separate from native task success in the output schema and reports.

Only the local **Python 3.13.5** environment was executed. A CI matrix for Python 3.11,
3.12, and 3.13 is included but was not run on GitHub here. The observed CPU dependency
versions are in `docs/CPU_TEST_ENVIRONMENT.json`; GPU environments follow their upstreams.

Recorded test output:

```text
86 passed in 3.44s
```

The generated example reports were produced by `physical-exec smoke`. They are labelled
software fixtures throughout; no robotics benchmark score is implied.
