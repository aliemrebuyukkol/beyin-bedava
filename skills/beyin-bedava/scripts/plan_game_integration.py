#!/usr/bin/env python3
"""Plan game integration and compare engine-neutral runtime evidence with its plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from detect_game_project import _collect_files, detect_engine
from task_ledger import file_path

RESOURCES = Path(__file__).resolve().parents[1] / "resources"
CATALOG_PATH = RESOURCES / "integration-catalog.json"
SCHEMA_PATH = RESOURCES / "integration.schema.json"
MANIFEST_NAME = "beyin-bedava.integration.json"
MAX_JSON_BYTES = 1_048_576


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def finite_number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"invalid JSON number: {value}")
    return number


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a regular file: {path}")
    with path.open("rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError(f"JSON file exceeds {MAX_JSON_BYTES} bytes: {path}")
    return json.loads(data, object_pairs_hook=unique_object, parse_float=finite_number,
                      parse_constant=finite_number)


def validate(kind, document, schema):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError("install jsonschema>=4.23,<5 to validate integration documents") from exc
    validator = Draft202012Validator(
        {"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"},
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    error = next(validator.iter_errors(document), None)
    if error:
        location = ".".join(map(str, error.absolute_path)) or "<root>"
        # Validation errors can contain raw payload values. Print only the location and rule.
        raise ValueError(f"{kind} at {location} violates {error.validator}")


def validate_comparator(spec):
    if not isinstance(spec, dict) or not spec:
        raise ValueError("comparator must be a nonempty object")
    allowed = {"lte", "lt", "gte", "gt", "approx", "tol", "between"}
    unknown = set(spec) - allowed
    if unknown:
        raise ValueError(f"unsupported comparator keys: {', '.join(sorted(unknown))}")
    if "between" in spec and len(spec) > 1:
        raise ValueError("between comparator cannot be combined with other operators")
    if "tol" in spec and "approx" not in spec:
        raise ValueError("tol requires approx comparator")
    if "approx" in spec and (set(spec) & {"lt", "lte", "gt", "gte"}):
        raise ValueError("approx cannot be combined with range operators")
    for key, val in spec.items():
        if key == "between":
            if (not isinstance(val, list) or len(val) != 2
                    or any(type(item) not in (int, float) or not math.isfinite(item) for item in val)
                    or val[0] > val[1]):
                raise ValueError("between requires two finite numbers [min, max] with min <= max")
        else:
            if type(val) not in (int, float) or not math.isfinite(val):
                raise ValueError(f"comparator {key} requires a finite number")
            if key == "tol" and val < 0:
                raise ValueError("comparator tol must be non-negative")


def index_checks(checks):
    result = {}
    for check in checks:
        cid = check["id"]
        if cid in result:
            raise ValueError("duplicate check ID")
        expect = check.get("expect")
        if isinstance(expect, dict):
            for val in expect.values():
                if isinstance(val, dict):
                    validate_comparator(val)
        result[cid] = check
    return result


def scoped_research(catalog, focus, engine, notes, schema):
    topics = {
        topic: {"question": rule["question"], "status": "unresearched", "sources": []}
        for topic, rule in catalog["topics"].items() if focus.intersection(rule["focus"])
    }
    engine_source = catalog["engine_sources"].get(engine)
    if "engine" in topics and engine_source:
        topics["engine"]["source_suggestions"] = [engine_source]
    validate("research", notes, schema)
    for note in notes:
        if note["topic"] not in catalog["topics"]:
            raise ValueError("unknown research topic")
        url = urlsplit(note["url"])
        if not url.hostname or url.username or url.password:
            raise ValueError("research sources require a hostname and no URL credentials")
        if date.fromisoformat(note["checked_on"]) > date.today():
            raise ValueError("research cannot be dated in the future")
        if note["topic"] in topics:
            item = topics[note["topic"]]
            item["sources"].append(note)
            item["status"] = "recorded"
    return topics


def plan_tasks(focus, topics, ownership):
    steps = [
        ("inspect", "Confirm the game root, owned source files, engine version, and existing test paths."),
    ]
    if topics:
        steps.append(("research", "Verify relevant primary sources, record findings and applicability, and identify unknowns."))
    if focus.intersection({"design", "experience", "progression", "economy", "simulation", "monetization"}):
        steps.append(("design", "Define player-facing acceptance criteria and preserve evidence provenance."))
    if "build" in focus:
        steps.append(("wire", "If implementation is authorized, use the existing game entry point and add the smallest required checks."))
    steps.append(("verify", "Run the relevant project checks and record their actual results and evidence limitations."))
    tasks = {name: {"id": name, "owner": "beyin-bedava", "acceptance": acceptance,
                    "depends": [steps[index - 1][0]] if index else [], "files": []}
             for index, (name, acceptance) in enumerate(steps)}
    owned = set()
    for task, path in ownership:
        if task not in tasks:
            raise ValueError(f"unknown task for file ownership: {task}")
        path = file_path(path)
        if path in owned:
            raise ValueError(f"file is already assigned: {path}")
        tasks[task]["files"].append(path)
        owned.add(path)
    return list(tasks.values())


def digest(plan):
    payload = {key: value for key, value in plan.items() if key != "plan_id"}
    content = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def create_plan(root, goal, focus, baseline, explicit_game, notes, catalog, schema, ownership=()):
    if not root.is_dir():
        raise ValueError("workspace directory not found")
    if not goal.strip() or not baseline.strip():
        raise ValueError("goal and baseline must be nonempty")
    chosen = set(focus)
    detected, engine, languages, signals = detect_engine(root, _collect_files(root))
    manifest_file = root / MANIFEST_NAME
    checks = []
    if manifest_file.exists() or manifest_file.is_symlink():
        manifest = read_json(manifest_file)
        validate("manifest", manifest, schema)
        index_checks(manifest["checks"])
        game = manifest["game"]
        checks = [check for check in manifest["checks"] if check["focus"] in chosen]
        basis = "declared_manifest"
    elif detected:
        game = {"name": root.name, "engine": engine}
        basis = "heuristic_detection"
    elif explicit_game:
        game = {"name": root.name, "engine": "unknown"}
        basis = "explicit_game_intent"
    else:
        raise ValueError("game could not be identified; select the game root or supply explicit game intent")

    modules = [
        {"path": entry["path"], "use": entry["use"]}
        for entry in catalog["modules"]
        if (chosen | {"core"}).intersection(entry["focus"])
        and ("engines" not in entry or game["engine"] in entry["engines"])
    ]
    topics = scoped_research(catalog, chosen, game["engine"], notes, schema)
    result = {
        "version": 1,
        "goal": goal,
        "baseline": baseline,
        "project": {**game, "basis": basis, "detector_engine": engine if detected else None,
                    "detector_evidence": signals, "languages": languages},
        "focus": sorted(chosen),
        "modules": modules,
        "research": topics,
        "tasks": plan_tasks(chosen, topics, ownership),
        "checks": checks,
    }
    result["plan_id"] = digest(result)
    return result


def same_value(expected, observed):
    if type(expected) is bool or type(observed) is bool:
        return type(expected) is type(observed) and expected == observed
    return expected == observed


def matches_expectation(expected, observed):
    if isinstance(expected, dict):
        if type(observed) not in (int, float) or not math.isfinite(observed):
            return False
        if "lte" in expected and not (observed <= expected["lte"]):
            return False
        if "lt" in expected and not (observed < expected["lt"]):
            return False
        if "gte" in expected and not (observed >= expected["gte"]):
            return False
        if "gt" in expected and not (observed > expected["gt"]):
            return False
        if "between" in expected:
            low, high = expected["between"]
            if not (low <= observed <= high):
                return False
        if "approx" in expected:
            tol = expected.get("tol", 1e-9)
            if abs(observed - expected["approx"]) > tol:
                return False
        return True
    return same_value(expected, observed)


def verify(plan, evidence, revision, schema):
    validate("evidence", evidence, schema)
    if (not isinstance(plan, dict) or type(plan.get("version")) is not int or plan["version"] != 1
            or plan.get("plan_id") != digest(plan)):
        raise ValueError("invalid integration plan or plan ID")
    if evidence["plan_id"] != plan["plan_id"]:
        raise ValueError("evidence belongs to a different plan")
    if evidence["revision"] != revision:
        raise ValueError("evidence revision does not match the specified build revision")
    checks = index_checks(plan["checks"])
    actual = index_checks(evidence["checks"])
    if actual.keys() - checks.keys():
        raise ValueError("evidence contains an out-of-scope check ID")

    outcomes = {}
    for key, check in checks.items():
        record = actual.get(key)
        if record is None:
            outcomes[key] = {"status": "missing"}
            continue
        expected, observed = check["expect"], record["observed"]
        missing = sorted(expected.keys() - observed.keys())
        mismatches = sorted(name for name in expected.keys() & observed.keys()
                            if not matches_expectation(expected[name], observed[name]))
        status = "failed" if mismatches else "missing" if missing else (
            "passed" if evidence["source"] == "runtime" else "synthetic_only")
        outcomes[key] = {"status": status, "missing": missing, "mismatches": mismatches,
                         "artifact": record["artifact"]}
    statuses = {outcome["status"] for outcome in outcomes.values()}
    status = "failed" if "failed" in statuses else "passed" if statuses == {"passed"} else "insufficient"
    return {"status": status, "plan_id": evidence["plan_id"], "revision": evidence["revision"],
            "source": evidence["source"], "checks": outcomes}


def main():
    catalog = read_json(CATALOG_PATH)
    schema = read_json(SCHEMA_PATH)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog")
    plan = commands.add_parser("plan")
    plan.add_argument("workspace", type=Path)
    plan.add_argument("--goal", required=True)
    plan.add_argument("--focus", choices=schema["$defs"]["focus"]["enum"], action="append")
    plan.add_argument("--baseline", default="unrecorded")
    plan.add_argument("--explicit-game", action="store_true")
    plan.add_argument("--research", type=Path)
    plan.add_argument("--own", nargs=2, action="append", default=[], metavar=("TASK", "PATH"))
    plan.add_argument("--output", type=Path)
    check = commands.add_parser("verify")
    check.add_argument("plan", type=Path)
    check.add_argument("evidence", type=Path)
    check.add_argument("--revision", required=True, help="independently identified build revision")
    args = parser.parse_args()
    try:
        if args.command == "catalog":
            result = catalog
        elif args.command == "plan":
            notes = read_json(args.research) if args.research else []
            result = create_plan(args.workspace.resolve(), args.goal, args.focus or ["build"],
                                 args.baseline, args.explicit_game, notes, catalog, schema, args.own)
            if args.output:
                with args.output.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream, indent=2, ensure_ascii=False)
                    stream.write("\n")
        else:
            result = verify(read_json(args.plan), read_json(args.evidence), args.revision, schema)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return {"passed": 0, "failed": 1, "insufficient": 2}[result["status"]] if args.command == "verify" else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        print(f"Integration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
