#!/usr/bin/env python3
"""Summarize measured tracking, not object localization or grasp success."""
import argparse
import json
from pathlib import Path
import numpy as np


def audit(run):
    events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
    receipts = [e["data"] for e in events if e["kind"] == "execution_receipt"]
    errors = [r["tracking_position_error_m"] for r in receipts
              if r.get("tracking_position_error_m") is not None]
    rejections = [e["data"]["reason"] for e in events
                  if e["kind"] == "input_rejected_no_execution"]
    decisions = [e["data"]["public_decision"] for e in events if e["kind"] == "decision"]
    return {
        "run": run.name,
        "executed_chunks": len(receipts),
        "endpoint_error_m": None if not errors else {
            "median": float(np.median(errors)), "max": float(max(errors)),
            "last": float(errors[-1]), "over_1cm": sum(x > .01 for x in errors),
            "count": len(errors),
        },
        "rejections": rejections,
        "final_model_assessment_not_ground_truth": decisions[-1].get("assessment") if decisions else None,
        "limitation": "Endpoint tracking error cannot measure target localization error or establish contact.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    args = parser.parse_args()
    print(json.dumps([audit(run) for run in args.runs], indent=2))


if __name__ == "__main__":
    main()
