"""Single-episode runner. Never reset, reroll, or retry ambiguous execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import time
from uuid import uuid4
from .contracts import Evaluation
from .controllers.ports import ControllerPort
from .errors import InputRejected, BudgetExceeded, AmbiguousExecution, ProviderError
from .safety import validate_chunk
from .trace import TraceWriter, dumps


@dataclass(frozen=True)
class RunBudget:
    max_decisions: int = 100
    max_control_steps: int = 1800
    max_wall_seconds: float = 1800
    max_consecutive_rejections: int = 2

    def __post_init__(self):
        if min(self.max_decisions, self.max_control_steps, self.max_wall_seconds) <= 0 or self.max_consecutive_rejections < 0:
            raise ValueError("invalid run budget")


def run_episode(env, controller: ControllerPort, output: str | Path, seed: int,
                budget: RunBudget, manifest_extra: dict | None = None, reference_run: str | Path | None = None,
                allow_related_reference: bool = False) -> Path:
    metadata = env.metadata()
    if metadata.get("backend") not in ("fixture", "embodiedswe") or metadata.get("real_hardware_supported") is not False:
        raise ValueError("this runner accepts only the audited simulation/fixture backends, never real hardware")
    manifest = {"software": "physical-exec/0.1.0", **(manifest_extra or {}), **metadata,
                "seed": seed, "controller_mode": controller.mode, "port_not_upstream_reproduction": True,
                "limits": asdict(controller.limits), "memory": asdict(controller.memory.config),
                "budget": asdict(budget), "policy_input_allowlist": ["RGB", "robot joints", "robot EEF pose",
                "measured gripper aperture", "task text", "execution receipts", "robot-only FK"],
                "privileged_policy_inputs": False, "model_tools": ["Act"],
                "scope": "SIMULATION ONLY; no certified safety or real-robot execution"}
    trace = TraceWriter(output, manifest)
    start = time.monotonic(); decisions = 0; rejections = 0; consecutive = 0; steps = 0
    evaluation = Evaluation(); terminal = "not_started"; error = None; source_steps = {}
    provider = controller.provider; obs = None
    try:
        obs = env.reset(seed)
        controller.memory.reset(); controller.memory.observe(obs)
        if reference_run:
            from .memory import reference_from_run
            controller.memory.references = reference_from_run(reference_run, obs.robot, obs.task,
                allow_related_task=allow_related_reference, expected_dt=obs.control_dt, expected_eef_frame=obs.eef_frame)
            trace.event("reference_loaded", {"source_run": str(Path(reference_run).resolve()),
                        "related_task_opt_in": allow_related_reference})
        trace.observation(obs)
        manifest["task_instruction"] = obs.task; manifest["robot"] = obs.robot
        manifest["eef_frame"] = obs.eef_frame
        manifest["action_convention"] = "world_xyz_wxyz_gripper_open"
        from .trace import write_json
        manifest = {**manifest, "trace_schema": "physical-exec/v1"}
        write_json(trace.path/"manifest.json", manifest)
        trace.event("run_manifest", manifest)
        evaluation = env.evaluate()
        if evaluation.success:
            terminal = "already_terminal_at_reset"
        else:
            while True:
                elapsed = time.monotonic()-start
                if elapsed >= budget.max_wall_seconds: terminal = "wall_budget"; break
                if decisions >= budget.max_decisions: terminal = "decision_budget"; break
                if steps >= budget.max_control_steps: terminal = "control_budget"; break
                decisions += 1
                try:
                    decision = controller.decide(obs, timeout_seconds=budget.max_wall_seconds-elapsed)
                    if decision.proposal is not None:
                        trace.event("proposal", decision.proposal.public())
                    trace.decision(decision.raw, decision.action, decision.usage)
                    if decision.action is None:
                        terminal = "model_stopped_incomplete"; break
                    action = validate_chunk(decision.action, obs, controller.limits)
                    remaining = budget.max_control_steps-steps
                    if len(action.values) > remaining:
                        # Explicit HOST budget truncation, recorded; not an unlogged policy edit.
                        trace.event("host_prefix_limit", {"requested": len(action.values), "execute": remaining})
                        action = action.prefix(remaining)
                    if time.monotonic()-start >= budget.max_wall_seconds:
                        terminal = "wall_budget_before_execution"; break
                    command_id = uuid4().hex
                    trace.event("execution_requested", {"command_id": command_id, "action": action.to_dict()})
                    result = env.step(action, command_id)
                except InputRejected as e:
                    rejections += 1; consecutive += 1
                    reply = controller.last_reply
                    trace.event("input_rejected_no_execution", {"reason": str(e),
                                "decision": reply.arguments if reply else None,
                                "usage": asdict(reply.usage) if reply else None, "observation_id": obs.key})
                    controller.memory.reject(str(e) + (" Previous requested decision: "+dumps(reply.arguments) if reply else ""))
                    if consecutive > budget.max_consecutive_rejections:
                        terminal = "rejection_budget"; break
                    continue
                if result.receipt.observation_id != obs.key or result.receipt.executed_steps < 1:
                    raise AmbiguousExecution("invalid execution acknowledgement; stop without retry")
                trace.execution(result)
                controller.memory.commit(obs, result.observation, action, result.receipt, decision.raw)
                obs = result.observation
                steps += result.receipt.executed_steps
                source_steps[action.source] = source_steps.get(action.source, 0)+result.receipt.executed_steps
                evaluation = result.evaluation; consecutive = 0
                if evaluation.success:
                    terminal = "native_success" if evaluation.native else "fixture_complete_not_robot_success"
                    break
    except BudgetExceeded as e:
        terminal = "provider_budget"; error = str(e)
    except AmbiguousExecution as e:
        terminal = "ambiguous_execution_halted"; error = str(e)
    except ProviderError as e:
        terminal = "provider_error"; error = str(e)
    except Exception as e:
        terminal = "runtime_error"; error = f"{type(e).__name__}: {e}"
    finally:
        usage = getattr(provider, "usage_log", [])
        totals = {name: sum(getattr(x, name) for x in usage) for name in
                  ("calls", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "latency_seconds")}
        totals["total_tokens"] = totals["input_tokens"]+totals["output_tokens"]
        totals["uncached_input_tokens"] = max(0, totals["input_tokens"]-totals["cached_input_tokens"])
        totals["reasoning_tokens_are_subset_of_output"] = True
        totals["billable_cost"] = None
        totals["all_usage_reported"] = all(u.usage_reported for u in usage)
        totals["provider_attempts"] = getattr(provider, "calls", 0) if metadata.get("backend") != "fixture" else 0
        result = {"terminal_reason": terminal, "error": error,
                  "native_success": bool(evaluation.native and evaluation.success and steps > 0 and terminal == "native_success"),
                  "environment_success_host_only": bool(evaluation.native and evaluation.success),
                  "fixture_pass": bool(metadata.get("backend") == "fixture" and evaluation.success),
                  "score_host_only": evaluation.score, "evaluation_note": evaluation.note,
                  "wall_seconds": time.monotonic()-start, "simulated_seconds": obs.sim_time if obs else 0,
                  "decision_count": decisions, "executed_control_steps": steps, "rejections": rejections,
                  "steps_by_source": source_steps, "usage": totals,
                  "memory_audit": controller.memory.anchors.snapshot(),
                  "privileged_policy_inputs": False, "recovery_claim": "not automatically inferred; inspect evidence",
                  "valid_robot_result": bool(evaluation.native and steps > 0 and terminal not in ("runtime_error", "ambiguous_execution_halted", "provider_error", "already_terminal_at_reset"))}
        trace.finish(result)
        try: env.close()
        finally:
            provider.close()
            if controller.proposer is not None and hasattr(controller.proposer, "close"):
                controller.proposer.close()
    return trace.path
