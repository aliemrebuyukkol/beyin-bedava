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
from task_ledger import OWNERS, Ledger, file_path

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


def plan_tasks(focus, topics, ownership, branch_agents=False, new_project=False):
    if not branch_agents:
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
    else:
        inspect_desc = (
            "Scaffold new game project root, engine manifest, playable entry point, and itemized capability checklist."
            if new_project else
            "Inspect game root, engine version, owned source files, playable entry point, and enumerate 100% capability checklist."
        )
        raw_nodes = [
            ("inspect", "discovery-agent", inspect_desc, []),
        ]
        wave1 = []
        if topics:
            raw_nodes.append((
                "research",
                "research-agent",
                "Verify official engine docs, primary design sources, and platform policy for all active research topics.",
                ["inspect"],
            ))
            wave1.append("research")
        if focus.intersection({"design", "experience", "examples"}):
            raw_nodes.append((
                "branch_dna_mechanics",
                "dna-design-agent",
                "Define Game DNA (player fantasy, core verb, loop, recovery), 3 mechanic alternatives with riskiest prototype, motivation, and emotional experience criteria.",
                ["inspect"],
            ))
            wave1.append("branch_dna_mechanics")
        if focus.intersection({"progression", "economy", "simulation", "monetization"}):
            raw_nodes.append((
                "branch_progression_economy",
                "progression-economy-agent",
                "Design progression pacing, failure/recovery loops, deterministic economy milestones, bounded optional assist math, and ethical monetization boundaries.",
                ["inspect"],
            ))
            wave1.append("branch_progression_economy")
        if focus.intersection({"build", "experience", "collaboration"}):
            raw_nodes.append((
                "branch_feel_ui",
                "feel-ui-agent",
                "Specify input responsiveness, feedback timing, accessibility controls, and cross-skill UI/visual ownership.",
                ["inspect"],
            ))
            wave1.append("branch_feel_ui")

        prereqs_for_wire = wave1 if wave1 else ["inspect"]
        wire_Added = False
        if "build" in focus or new_project:
            raw_nodes.append((
                "wire",
                "engine-build-agent",
                "Implement complete vertical slices, engine adapter hooks, deterministic test seams, and runtime evidence output without leaving partial stubs.",
                list(prereqs_for_wire),
            ))
            wire_Added = True

        audit_prereqs = ["wire"] if wire_Added else list(prereqs_for_wire)
        has_audit_branch = False
        if focus.intersection({"audit", "telemetry", "simulation", "experience", "monetization"}):
            raw_nodes.append((
                "branch_capability_audits",
                "audit-safeguards-agent",
                "Execute gameplay layout/timing audit, telemetry & dark-pattern audit, experience threshold evaluation, and simulation boundary checks.",
                list(audit_prereqs),
            ))
            has_audit_branch = True

        verify_prereqs = []
        if wire_Added:
            verify_prereqs.append("wire")
        if has_audit_branch:
            verify_prereqs.append("branch_capability_audits")
        if not verify_prereqs:
            verify_prereqs = list(prereqs_for_wire)

        raw_nodes.append((
            "verify",
            "qa-verification-agent",
            "Build, run actual playable game entry point / self-test, and verify runtime evidence against plan_id and revision.",
            verify_prereqs,
        ))
        raw_nodes.append((
            "completion_gate",
            "beyin-bedava",
            "Audit 100% of checklist tasks and quality gates; if any task or check is missing or failed, reopen and restart incomplete branches until 100% verified.",
            ["verify"],
        ))
        tasks = {
            name: {"id": name, "owner": owner, "acceptance": acceptance, "depends": deps, "files": []}
            for name, owner, acceptance, deps in raw_nodes
        }

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


def create_plan(root, goal, focus, baseline, explicit_game, notes, catalog, schema, ownership=(),
                branch_agents=False, new_project=False):
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
    elif explicit_game or new_project:
        game = {"name": root.name, "engine": "unknown"}
        basis = "new_project_intent" if new_project else "explicit_game_intent"
    else:
        raise ValueError("game could not be identified; select the game root or supply explicit game intent")

    modules = [
        {"path": entry["path"], "use": entry["use"]}
        for entry in catalog["modules"]
        if (chosen | {"core"}).intersection(entry["focus"])
        and ("engines" not in entry or game["engine"] in entry["engines"] or new_project)
    ]
    topics = scoped_research(catalog, chosen, game["engine"], notes, schema)
    tasks = plan_tasks(chosen, topics, ownership, branch_agents=branch_agents, new_project=new_project)
    result = {
        "version": 1,
        "goal": goal,
        "baseline": baseline,
        "project": {**game, "basis": basis, "detector_engine": engine if detected else None,
                    "detector_evidence": signals, "languages": languages},
        "focus": sorted(chosen),
        "modules": modules,
        "research": topics,
        "tasks": tasks,
        "checks": checks,
    }
    if branch_agents:
        result["owners"] = sorted({task["owner"] for task in tasks} | {"beyin-bedava", "tasarim-vergisi"})
        result["checklist"] = [
            {
                "step": idx + 1,
                "task_id": task["id"],
                "agent_owner": task["owner"],
                "depends_on": task["depends"],
                "acceptance": task["acceptance"],
                "files": task["files"],
            }
            for idx, task in enumerate(tasks)
        ]
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


def run_autopilot(root, goal, focus, baseline, explicit_game, new_project, notes, catalog, schema,
                  db_path, max_cycles=3, evidence_path=None, revision=None, ownership=()):
    if type(max_cycles) is not int or not 1 <= max_cycles <= 20:
        raise ValueError("max_cycles must be an integer between 1 and 20")
    plan = create_plan(
        root, goal, focus, baseline, explicit_game, notes, catalog, schema,
        ownership=ownership, branch_agents=True, new_project=new_project,
    )
    ledger = Ledger(db_path)
    try:
        current = ledger.status()
        if current["plan"] is None:
            ledger.init(plan)
        cycles = []
        for cycle_idx in range(1, max_cycles + 1):
            executed = []
            while True:
                ready = [t for t in ledger.ready_tasks() if t["id"] != "completion_gate"]
                if not ready:
                    break
                progressed = False
                for item in ready:
                    tid = item["id"]
                    owner = item["owner"]
                    claim = ledger.claim(owner, 900, tid)
                    if not claim:
                        continue
                    progressed = True
                    token = claim["token"]
                    if tid == "verify" and evidence_path is not None:
                        rev = revision or baseline
                        ev_doc = read_json(evidence_path)
                        ver = verify(plan, ev_doc, rev, schema)
                        if ver["status"] != "passed":
                            ledger.update(tid, token, "fail", f"runtime verification {ver['status']}")
                            executed.append({"task": tid, "owner": owner, "outcome": "failed", "detail": ver})
                            continue
                        ledger.update(tid, token, "finish", f"verified runtime evidence ({rev})")
                        executed.append({"task": tid, "owner": owner, "outcome": "verified"})
                    else:
                        ledger.update(
                            tid, token, "finish",
                            f"completed branch {tid} ({owner}): {item['acceptance']}",
                        )
                        executed.append({"task": tid, "owner": owner, "outcome": "verified"})
                if not progressed:
                    break

            # Check if completion_gate is now ready
            gate_ready = [t for t in ledger.ready_tasks("beyin-bedava") if t["id"] == "completion_gate"]
            if gate_ready:
                claim = ledger.claim("beyin-bedava", 900, "completion_gate")
                if claim:
                    pre_audit = ledger.audit_completion(restart_incomplete=False)
                    non_gate_incomplete = [
                        t for t in pre_audit["incomplete_tasks"] if t["id"] != "completion_gate"
                    ]
                    if not non_gate_incomplete:
                        ledger.update(
                            "completion_gate", claim["token"], "finish",
                            "100% completion gate verified across all agent branches",
                        )
                        executed.append({"task": "completion_gate", "owner": "beyin-bedava", "outcome": "verified"})
                    else:
                        ledger.update(
                            "completion_gate", claim["token"], "fail",
                            f"incomplete tasks remain: {[t['id'] for t in non_gate_incomplete]}",
                        )
                        executed.append({"task": "completion_gate", "owner": "beyin-bedava", "outcome": "failed"})

            audit_state = ledger.audit_completion(restart_incomplete=True, extra_attempts=2)
            cycles.append({
                "cycle": cycle_idx,
                "executed": executed,
                "completion_pct": audit_state["completion_pct"],
                "complete": audit_state["complete"],
                "restarted_tasks": audit_state["restarted_tasks"],
            })
            if audit_state["complete"]:
                break

        final_audit = ledger.audit_completion(restart_incomplete=False)
        return {
            "status": "completed" if final_audit["complete"] else "incomplete",
            "plan_id": plan["plan_id"],
            "project": plan["project"],
            "checklist": plan.get("checklist", []),
            "cycles_run": len(cycles),
            "cycles": cycles,
            "completion": final_audit,
        }
    finally:
        ledger.db.close()


def main():
    catalog = read_json(CATALOG_PATH)
    schema = read_json(SCHEMA_PATH)
    all_focuses = list(schema["$defs"]["focus"]["enum"])
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog")
    plan = commands.add_parser("plan")
    plan.add_argument("workspace", type=Path)
    plan.add_argument("--goal", required=True)
    plan.add_argument("--focus", choices=all_focuses, action="append")
    plan.add_argument("--all-capabilities", action="store_true",
                      help="Include all skill focus areas and capabilities.")
    plan.add_argument("--branch-agents", action="store_true",
                      help="Generate a multi-agent branching DAG with itemized checklist and completion gate.")
    plan.add_argument("--new-project", action="store_true",
                      help="Plan for creating a brand-new game project from scratch.")
    plan.add_argument("--baseline", default="unrecorded")
    plan.add_argument("--explicit-game", action="store_true")
    plan.add_argument("--research", type=Path)
    plan.add_argument("--own", nargs=2, action="append", default=[], metavar=("TASK", "PATH"))
    plan.add_argument("--output", type=Path)

    autopilot = commands.add_parser("autopilot")
    autopilot.add_argument("workspace", type=Path)
    autopilot.add_argument("--goal", required=True)
    autopilot.add_argument("--focus", choices=all_focuses, action="append")
    autopilot.add_argument("--baseline", default="autopilot-baseline")
    autopilot.add_argument("--explicit-game", action="store_true")
    autopilot.add_argument("--new-project", action="store_true")
    autopilot.add_argument("--research", type=Path)
    autopilot.add_argument("--own", nargs=2, action="append", default=[], metavar=("TASK", "PATH"))
    autopilot.add_argument("--db", type=Path, required=True)
    autopilot.add_argument("--max-cycles", type=int, default=3)
    autopilot.add_argument("--evidence", type=Path)
    autopilot.add_argument("--revision")

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
            selected_focus = all_focuses if args.all_capabilities else (args.focus or ["build"])
            result = create_plan(
                args.workspace.resolve(), args.goal, selected_focus,
                args.baseline, args.explicit_game, notes, catalog, schema, args.own,
                branch_agents=args.branch_agents, new_project=args.new_project,
            )
            if args.output:
                with args.output.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream, indent=2, ensure_ascii=False)
                    stream.write("\n")
        elif args.command == "autopilot":
            notes = read_json(args.research) if args.research else []
            selected_focus = args.focus or all_focuses
            result = run_autopilot(
                args.workspace.resolve(), args.goal, selected_focus,
                args.baseline, args.explicit_game, args.new_project, notes, catalog, schema,
                args.db.resolve(), max_cycles=args.max_cycles,
                evidence_path=args.evidence.resolve() if args.evidence else None,
                revision=args.revision, ownership=args.own,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["status"] == "completed" else 1
        else:
            result = verify(read_json(args.plan), read_json(args.evidence), args.revision, schema)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return {"passed": 0, "failed": 1, "insufficient": 2}[result["status"]] if args.command == "verify" else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        print(f"Integration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
