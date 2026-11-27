#!/usr/bin/env python3
"""Run the Beyin-Bedava 2.1 paired benchmark on Yankı Rotası's movement contract."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beyin-repo", type=Path, required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = importlib.util.spec_from_file_location("beyin_benchmark", args.beyin_repo / "benchmarks/run.py")
    bench = importlib.util.module_from_spec(module)
    module.loader.exec_module(bench)
    skill = args.beyin_repo / "skills/beyin-bedava"
    context = "\n\n".join((skill / relative).read_text() for relative in bench.MODULES)
    domains = [range(6), range(4), range(3), range(2)]
    cases = []
    for tile, move, echo, powered in itertools.product(*domains):
        allowed = (tile == 0 or tile == 2 and echo == 1 or tile == 3 and echo == 2
                   or tile == 4 and move == 1 or tile == 5 and powered == 1)
        cases.append(([tile, move, echo, powered], int(allowed)))
    task = {
        "id": "yanki-gate",
        "brief": ("Return integer 1 if the player can enter a tile, otherwise 0. "
                  "tile 0 is open floor, 1 is a wall, 2 is gate A, 3 is gate B, "
                  "4 is a one-way marker, 5 is a powered gate. Move 1 means east. "
                  "Echo 0 means none, 1 holds A, 2 holds B. powered 1 means the battery has been collected. "
                  "Only the matching echo opens A or B. The one-way tile accepts eastward entry. "
                  "The powered gate opens after collecting the battery. "
                  "Propose three alternative puzzle rules that keep mobile feedback readable."),
        "names": ["tile", "move", "echo", "powered"],
        "domains": [list(domain) for domain in domains],
        "cases": cases,
        "bounds": [0, 1],
    }
    pairs = []
    for _, repeat, order, seed in bench.paired_schedule([task], 2, 42):
        pair = {"task": task["id"], "repeat": repeat + 1, "order": order, "seed": seed}
        for condition in order:
            prompt = bench.prompt_for(task, context if condition == "on" else "")
            result = bench.chat_run(prompt, args.model, 90, args.endpoint, None, seed)
            if result["status"] == "completed":
                try:
                    result.update(bench.grade(result["answer"], task))
                except ValueError:
                    result.update(status="invalid_output", creativity_proxy=0, code_quality=0,
                                  task_completion=0, error_rate=1)
            pair[condition] = result
        pairs.append(pair)
    summary = bench.aggregate(pairs)
    args.output.write_text(json.dumps({
        "model": args.model, "conditions": "counterbalanced_skill_context", "acceptance_cases": len(cases),
        "summary": summary, "pairs": pairs,
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return int(summary["completed_pairs"] != len(pairs))


if __name__ == "__main__":
    raise SystemExit(main())
