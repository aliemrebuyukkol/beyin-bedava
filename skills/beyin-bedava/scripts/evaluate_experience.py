#!/usr/bin/env python3
"""Evaluate preregistered game experience criteria against aggregate observations."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# Unit, direction and accepted evidence sources. Thresholds belong to each playtest plan.
CRITERIA = {
    "meaningful_choice_rate": ("ratio", "min", {"human_playtest"}),
    "voluntary_retry_rate": ("ratio", "min", {"human_playtest"}),
    "distinct_mechanic_alternatives": ("count", "min", {"design_review", "human_playtest"}),
    "distinct_successful_strategies": ("count", "min", {"human_playtest"}),
    "input_feedback_p95_ms": ("ms", "max", {"instrumented_runtime", "human_playtest"}),
    "missed_input_rate": ("ratio", "max", {"instrumented_runtime", "human_playtest"}),
    "target_emotion_rate": ("ratio", "min", {"human_playtest"}),
    "unintended_distress_rate": ("ratio", "max", {"human_playtest"}),
}


def number(value, unit):
    if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
            or (unit == "ratio" and value > 1) or (unit == "count" and type(value) is not int)):
        raise ValueError(f"invalid {unit} measure: {value}")
    return value


def evaluate(document):
    plan, observations = document["plan"], document["observations"]
    if not isinstance(plan, dict) or not plan or not isinstance(observations, dict):
        raise ValueError("a nonempty plan and an observations object are required")
    if set(observations) - plan.keys():
        raise ValueError("observations must be declared in the plan")
    results = {}
    for name, criterion in plan.items():
        unit, direction, sources = CRITERIA[name]
        threshold = number(criterion["threshold"], unit)
        minimum = criterion["min_samples"]
        if type(minimum) is not int or minimum < 1:
            raise ValueError(f"{name}: invalid minimum sample count")
        for key in ("method", "population"):
            if not isinstance(criterion[key], str) or not criterion[key].strip():
                raise ValueError(f"{name}: declare {key}")
        entry = {"threshold": threshold, "unit": unit, "direction": direction}
        observation = observations.get(name)
        if observation is None:
            entry["status"] = "missing"
        else:
            source, value, sample_size, reference = (observation[key] for key in
                                                    ("source", "value", "sample_size", "reference"))
            number(value, unit)
            if source not in sources | {"synthetic"}:
                raise ValueError(f"{name}: incompatible evidence source")
            if not isinstance(reference, str) or not reference.strip() or type(sample_size) is not int or sample_size < 1:
                raise ValueError(f"{name}: evidence reference and positive sample size required")
            status = "synthetic_only" if source == "synthetic" else "insufficient"
            if source != "synthetic" and sample_size >= minimum:
                met = value >= threshold if direction == "min" else value <= threshold
                status = "met" if met else "missed"
            entry.update(status=status, source=source, value=value, sample_size=sample_size, reference=reference)
        results[name] = entry
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, KeyError, ValueError, TypeError, AttributeError, OverflowError) as exc:
        parser.exit(2, f"Invalid experience evidence: {exc}\n")
    print(json.dumps(result, indent=2))
    states = {item["status"] for item in result.values()}
    return 1 if "missed" in states else int(states != {"met"}) * 2


if __name__ == "__main__":
    sys.exit(main())
