#!/usr/bin/env python3
"""Validate the game's opt-in aggregate and screen undersampled results."""
import argparse
import json
import math
from pathlib import Path

COUNTERS = {"actions", "blocked", "hints", "undos", "resets", "wins"}
MIN_SAMPLES = 30


def validate(document):
    if not isinstance(document, dict) or type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ValueError("expected version 1 session")
    source = document["source"]
    if source not in ("observed_local", "synthetic"):
        raise ValueError("source must be declared")
    if set(document) != {"schema_version", "source", "levels", "render_feedback"}:
        raise ValueError("unexpected or missing top-level fields")
    levels = document["levels"]
    if not isinstance(levels, dict):
        raise ValueError("levels must be an object")
    flags = {}
    for level, row in levels.items():
        if level not in {"1", "2", "3", "4", "5", "6"} or not isinstance(row, dict) or set(row) != COUNTERS:
            raise ValueError(f"malformed level: {level}")
        if any(type(value) is not int or value < 0 for value in row.values()):
            raise ValueError(f"invalid count in level {level}")
        if sum(row[key] for key in COUNTERS - {"actions"}) > row["actions"]:
            raise ValueError(f"counter totals exceed aggregate actions in level {level}")
        rule_actions = row["actions"] - row["hints"] - row["undos"] - row["resets"]
        if rule_actions < MIN_SAMPLES:
            flags[level] = "insufficient"
        elif row["blocked"] / rule_actions >= 0.5:
            flags[level] = "review_blocked_actions"
        else:
            flags[level] = "no_screening_signal"
    feedback = document["render_feedback"]
    if not isinstance(feedback, dict) or set(feedback) != {"samples_ms", "p95_ms"}:
        raise ValueError("invalid render data")
    times = feedback["samples_ms"]
    if not isinstance(times, list) or len(times) > 128 or any(
        type(value) not in (int, float) or not 0 <= value <= 2000 or not math.isfinite(value) for value in times
    ):
        raise ValueError("invalid render samples")
    percentile = feedback["p95_ms"]
    if len(times) < MIN_SAMPLES:
        if percentile is not None:
            raise ValueError("p95 requires at least 30 samples")
    else:
        expected = sorted(times)[math.ceil(len(times) * 0.95) - 1]
        if type(percentile) not in (float, int) or not math.isclose(percentile, expected, rel_tol=1e-7, abs_tol=1e-7):
            raise ValueError("p95 does not match the reported samples")
    return {"source": source, "coverage": "synthetic_only" if source == "synthetic" else "single_local_session",
            "level_screens": flags, "render_sample_count": len(times), "render_p95_ms": percentile}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, KeyError, ValueError, TypeError, OverflowError) as exc:
        parser.exit(2, f"Invalid session evidence: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
