#!/usr/bin/env python3
"""Run paired model game-design and rules tasks with and without selected skill context."""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parent / "skills" / "beyin-bedava"
MODULES = ("SKILL.md", "intelligence/creative-mechanics.md", "intelligence/game-feel.md")
AXES = {"timing", "position", "resource", "sequence", "discovery", "cooperation"}
METRICS = ("creativity_proxy", "code_quality", "task_completion", "error_rate",
           "input_tokens", "cached_input_tokens", "output_tokens", "total_tokens", "seconds")
EXPRESSION_NODES = (
    ast.Expression, ast.Constant, ast.Name, ast.Load, ast.IfExp, ast.Compare,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.BoolOp, ast.And,
    ast.Or, ast.UnaryOp, ast.Not, ast.USub, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
    ast.FloorDiv, ast.Mod, ast.Call,
)
FUNCTIONS = {"min": min, "max": max, "abs": abs}


def compile_rule(expression, names):
    if not isinstance(expression, str) or len(expression) > 500:
        raise ValueError("expression missing or too long")
    tree = ast.parse(expression.strip(), mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, EXPRESSION_NODES):
            raise ValueError("expression uses unsupported syntax")
        if isinstance(node, ast.Constant) and (type(node.value) is not int or abs(node.value) > 1000):
            raise ValueError("only small integer literals are accepted")
        if isinstance(node, ast.Name) and node.id not in names and node.id not in FUNCTIONS:
            raise ValueError("unknown identifier")
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS
                                         or node.keywords or len(node.args) not in (1, 2, 3)):
            raise ValueError("unsupported function call")
    return compile(tree, "<benchmark-rule>", "eval"), sum(isinstance(n, ast.IfExp) for n in ast.walk(tree))


def grade(answer, task):
    document = json.loads(answer)
    if not isinstance(document, dict):
        raise ValueError("model output must be an object")
    mechanics = document.get("mechanics")
    valid = set()
    rules = set()
    if isinstance(mechanics, list):
        for idea in mechanics[:3]:
            fields = ("rule", "player_choice", "feedback")
            if (isinstance(idea, dict) and isinstance(idea.get("axis"), str) and idea["axis"] in AXES
                    and all(isinstance(idea.get(field), str) and len(idea[field].split()) >= 3 for field in fields)):
                normalized = " ".join(idea["rule"].lower().split())
                if normalized not in rules:
                    valid.add(idea["axis"])
                    rules.add(normalized)
    creativity = len(valid) / 3
    try:
        code, branches = compile_rule(document.get("expression"), set(task["names"]))
    except (ValueError, SyntaxError):
        return {"creativity_proxy": creativity, "code_quality": 0, "task_completion": 0, "error_rate": 1}
    results = {}
    errors = 0
    lower, upper = task["bounds"]
    for values in itertools.product(*task["domains"]):
        try:
            result = eval(code, {"__builtins__": {}, **FUNCTIONS}, dict(zip(task["names"], values)))
            if type(result) is not int or not lower <= result <= upper:
                raise ValueError("result is out of contract")
            results[values] = result
        except (ArithmeticError, TypeError, ValueError):
            errors += 1
    error_rate = errors / (errors + len(results))
    passed = sum(results.get(tuple(arguments)) == expected for arguments, expected in task["cases"])
    return {"creativity_proxy": creativity, "code_quality": (1 + (1 - error_rate) + (branches <= 4)) / 3,
            "task_completion": passed / len(task["cases"]), "error_rate": error_rate}


def codex_run(prompt, model, timeout):
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="beyin-benchmark-") as work:
        command = ["codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
                   "--skip-git-repo-check", "--sandbox", "read-only", "--json", "--model", model, "-"]
        try:
            process = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                     cwd=work, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "provider_error", "error": type(exc).__name__,
                    "seconds": round(time.perf_counter() - started, 4)}
    seconds = round(time.perf_counter() - started, 4)
    events = []
    for line in process.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    answers = [event["item"]["text"] for event in events if event.get("type") == "item.completed"
               and event.get("item", {}).get("type") == "agent_message"]
    if process.returncode or not usage or not answers:
        auth_error = any(term in (process.stdout + process.stderr).lower()
                         for term in ("401 unauthorized", "sign in again", "authentication token", "access token"))
        return {"status": "provider_error", "error": "authentication" if auth_error else "incomplete_turn",
                "exit_code": process.returncode, "seconds": seconds}
    tokens = {}
    for field in ("input_tokens", "cached_input_tokens", "output_tokens"):
        values = [item.get(field) for item in usage]
        tokens[field] = sum(values) if all(type(value) is int and value >= 0 for value in values) else None
    tokens["total_tokens"] = (tokens["input_tokens"] + tokens["output_tokens"]
                              if tokens["input_tokens"] is not None and tokens["output_tokens"] is not None else None)
    return {"status": "completed", "answer": answers[-1], "seconds": seconds, **tokens}


def chat_run(prompt, model, timeout, endpoint, key, seed):
    idea = {"type": "object", "additionalProperties": False,
            "properties": {"axis": {"type": "string", "enum": sorted(AXES)},
                           **{field: {"type": "string"} for field in ("rule", "player_choice", "feedback")}},
            "required": ["axis", "rule", "player_choice", "feedback"]}
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"expression": {"type": "string"},
                             "mechanics": {"type": "array", "items": idea, "minItems": 3, "maxItems": 3}},
              "required": ["expression", "mechanics"]}
    request = Request(endpoint, data=json.dumps({
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 650, "seed": seed,
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "game_task", "strict": True, "schema": schema}},
    }).encode("utf-8"), headers={"Content-Type": "application/json"})
    if key:
        request.add_unredirected_header("Authorization", f"Bearer {key}")
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        answer = payload["choices"][0]["message"]["content"]
        usage = payload["usage"]
        tokens = {"input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"],
                  "cached_input_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
                  "total_tokens": usage["total_tokens"]}
        if (not isinstance(answer, str) or any(type(tokens[field]) is not int or tokens[field] < 0
                                              for field in ("input_tokens", "output_tokens", "total_tokens"))):
            raise ValueError("provider returned invalid answer or token usage")
        result = {"status": "completed", "answer": answer, **tokens}
    except HTTPError as exc:
        result = {"status": "provider_error", "error": f"HTTP {exc.code}"}
    except (URLError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        result = {"status": "provider_error", "error": type(exc).__name__}
    return {**result, "seconds": round(time.perf_counter() - started, 4)}


def prompt_for(task, context=""):
    return (
        "Solve this self-contained game design benchmark. Work from the supplied prompt only. "
        "Do not call tools or read workspace files. Return a JSON object with expression (a single Python "
        "integer expression using the named variables, comparisons, arithmetic, min/max/abs or ternaries) "
        "and mechanics (three distinct objects, each with axis, rule, player_choice, feedback). "
        f"Allowed axes: {', '.join(sorted(AXES))}. Write each rule, choice and feedback as a concrete phrase.\n"
        f"Task: {task['brief']}\nInput variables: {', '.join(task['names'])}."
        + (f"\n\nSelected Beyin-Bedava skill context (apply to this task only):\n{context}" if context else "")
    )


def aggregate(pairs):
    complete = [pair for pair in pairs if all(pair[k]["status"] != "provider_error" for k in ("off", "on"))]
    metrics = {}
    for metric in METRICS:
        matched = [(pair["off"][metric], pair["on"][metric]) for pair in complete
                   if pair["off"].get(metric) is not None and pair["on"].get(metric) is not None]
        metrics[metric] = None
        if matched:
            off, on = zip(*matched)
            metrics[metric] = {"paired_n": len(matched), "off_mean": statistics.mean(off),
                               "on_mean": statistics.mean(on),
                               "paired_delta_on_minus_off": statistics.mean(b - a for a, b in matched)}
    return {"completed_pairs": len(complete), "metrics": metrics,
            "provider_error_rate": {condition: statistics.mean(p[condition]["status"] == "provider_error"
                                                               for p in pairs) for condition in ("off", "on")}}


def paired_schedule(tasks, repeats, seed):
    rng = random.Random(seed)
    schedule = []
    for task in tasks:
        first = rng.choice(("off", "on"))
        for repeat in range(repeats):
            second = "on" if first == "off" else "off"
            schedule.append((task, repeat, (first, second), rng.getrandbits(31)))
            first = second
    rng.shuffle(schedule)
    return schedule


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--chat-url", help="OpenAI-compatible /v1/chat/completions URL. Defaults to Codex CLI.")
    parser.add_argument("--api-key-env", help="Optional environment variable containing a provider key.")
    parser.add_argument("--model-revision", help="Artifact checksum or provider model revision for the report.")
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--task")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1 or args.timeout < 1:
        parser.error("positive repeats and timeout required")
    if args.chat_url:
        url = urlsplit(args.chat_url)
        if (not url.hostname or url.username or url.password or
                (url.scheme != "https" and (url.scheme != "http" or url.hostname not in {"127.0.0.1", "::1", "localhost"}))):
            parser.error("use HTTPS or a loopback HTTP server for chat inference")
    if args.api_key_env and (not args.chat_url or not os.environ.get(args.api_key_env)):
        parser.error("--api-key-env requires --chat-url and a populated environment variable")
    key = os.environ.get(args.api_key_env) if args.api_key_env else None
    task_bytes = (ROOT / "tasks.json").read_bytes()
    tasks = [task for task in json.loads(task_bytes) if args.task in (None, task["id"])]
    if not tasks:
        parser.error("unknown task")
    context = "\n\n".join((SKILL / path).read_text(encoding="utf-8") for path in MODULES)
    pairs = []
    for task, repeat, order, seed in paired_schedule(tasks, args.repeats, args.seed):
        seed = seed if args.chat_url else None
        pair = {"task": task["id"], "repeat": repeat + 1, "order": order, "inference_seed": seed}
        for condition in order:
            prompt = prompt_for(task, context if condition == "on" else "")
            if args.chat_url:
                result = chat_run(prompt, args.model, args.timeout, args.chat_url, key, seed)
            else:
                result = codex_run(prompt, args.model, args.timeout)
            if result["status"] == "completed":
                try:
                    result.update(grade(result["answer"], task))
                except (ValueError, RecursionError):
                    result.update(status="invalid_output", creativity_proxy=0, code_quality=0,
                                  task_completion=0, error_rate=1)
            pair[condition] = result
        pairs.append(pair)
    report = {"benchmark_kind": "openai_compatible_chat" if args.chat_url else "real_codex_cli",
              "model_requested": args.model, "model_revision": args.model_revision, "seed": args.seed,
              "condition_order": "counterbalanced_within_task",
              "repeats_per_task": args.repeats, "modules": MODULES, "timeout_seconds": args.timeout,
              "tasks_sha256": hashlib.sha256(task_bytes).hexdigest(),
              "skill_context_sha256": hashlib.sha256(context.encode()).hexdigest(),
              "summary": aggregate(pairs), "pairs": pairs}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["completed_pairs"] == len(pairs) else 2


if __name__ == "__main__":
    raise SystemExit(main())
