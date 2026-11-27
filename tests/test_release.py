import copy
import importlib.util
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "beyin-bedava" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import audit_gameplay
import audit_telemetry
import evaluate_experience
import install_skill
import simulate_eomm_dda
import task_ledger
from telemetry_validation import rebound_test, validate

SPEC = importlib.util.spec_from_file_location("release_benchmark", ROOT / "benchmarks/run.py")
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.path = pathlib.Path(scratch.name) / "tasks.db"
        self.ledger = task_ledger.Ledger(self.path)
        self.addCleanup(self.ledger.db.close)
        self.plan = {"goal": "Build a game", "baseline": "2a9e424", "tasks": [
            {"id": "game", "owner": "beyin-bedava", "acceptance": "play it",
             "files": ["game/core.py"], "max_attempts": 2},
            {"id": "hud", "owner": "tasarim-vergisi", "acceptance": "render it",
             "files": ["game/hud.py"], "depends": ["game"]},
        ]}

    def test_dependencies_checkpoint_recovery_and_stale_token(self):
        self.ledger.init(self.plan)
        self.assertIsNone(self.ledger.claim("tasarim-vergisi", 60))
        with patch.object(task_ledger.time, "time", return_value=100):
            first = self.ledger.claim("beyin-bedava", 1)
            self.ledger.update("game", first["token"], "checkpoint", '{"next":"run tests"}', 1)
            self.assertEqual(self.ledger.check_files("game", first["token"], ["game/core.py"]), ["game/core.py"])
            with self.assertRaisesRegex(ValueError, "unowned"):
                self.ledger.check_files("game", first["token"], ["game/hud.py"])
        resumed = task_ledger.Ledger(self.path)
        self.addCleanup(resumed.db.close)
        second = resumed.claim("beyin-bedava", 60)
        self.assertEqual(second["checkpoint"], {"next": "run tests"})
        self.assertEqual(second["previous_problem"], "worker lease expired")
        with self.assertRaisesRegex(ValueError, "current lease"):
            self.ledger.update("game", first["token"], "finish", "invalid")
        resumed.update("game", second["token"], "finish", "tests passed")
        self.assertEqual(self.ledger.claim("tasarim-vergisi", 60)["task"], "hud")

    def test_failure_budget_handoff_and_reopen(self):
        self.ledger.init(self.plan)
        for _ in range(2):
            task = self.ledger.claim("beyin-bedava", 60)
            self.ledger.update("game", task["token"], "fail", "build failed")
        self.assertIsNone(self.ledger.claim("beyin-bedava", 60))
        self.ledger.handoff("game", "tasarim-vergisi", "Transferred ownership")
        self.ledger.reopen("game", "Dependency repaired")
        self.assertEqual(self.ledger.claim("tasarim-vergisi", 60)["task"], "game")

    def test_ownership_conflict_rolls_back_and_cycles_rejected(self):
        conflict = copy.deepcopy(self.plan)
        conflict["tasks"][1]["files"] = ["game/core.py"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger.init(conflict)
        self.assertIsNone(self.ledger.status()["plan"])
        self.plan["tasks"][0]["depends"] = ["hud"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            self.ledger.init(self.plan)

    def test_concurrent_connections_cannot_claim_same_task(self):
        self.ledger.init(self.plan)
        second = task_ledger.Ledger(self.path)
        self.addCleanup(second.db.close)
        self.assertIsNotNone(self.ledger.claim("beyin-bedava", 60))
        self.assertIsNone(second.claim("beyin-bedava", 60))

    def test_canonical_files(self):
        for path in ("../file", "/file", "./file", "path//file", "path\\file"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                task_ledger.file_path(path)

    def test_custom_owners_reopen_attempts_and_git_worktree(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = pathlib.Path(scratch).resolve()
            db_path = root / "ledger.db"
            ledger = task_ledger.Ledger(db_path)
            self.addCleanup(ledger.db.close)
            plan = {
                "goal": "Custom owner slice",
                "baseline": "abc123",
                "owners": ["gameplay-agent", "qa-agent"],
                "tasks": [
                    {"id": "slice", "owner": "gameplay-agent", "acceptance": "ship it",
                     "files": ["src/game.py"], "max_attempts": 1},
                ],
            }
            ledger.init(plan)
            first = ledger.claim("gameplay-agent", 60)
            ledger.update("slice", first["token"], "fail", "first failure")
            self.assertIsNone(ledger.claim("gameplay-agent", 60))
            ledger.reopen("slice", "retry with budget", extra_attempts=3)
            reopened = ledger.claim("gameplay-agent", 60)
            self.assertEqual(reopened["task"], "slice")

            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src/game.py").write_text("print('ok')\n", encoding="utf-8")
            worktree = ledger.check_git_worktree("slice", reopened["token"], repo)
            self.assertEqual(worktree, {"owned": ["src/game.py"], "changed": ["src/game.py"]})

            (repo / "other.py").write_text("print('unowned')\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unowned files: other.py"):
                ledger.check_git_worktree("slice", reopened["token"], repo)


class GameplayTests(unittest.TestCase):
    def test_layout_balance_and_mechanic_coverage(self):
        rules = {"verb": "move", "feedback": "highlight", "failure": "wall", "recovery": "retry"}
        payload = {
            "mechanics": {"walk": rules, "unused": rules},
            "levels": [
                {"id": "a", "grid": ["S.K", "#.G"], "mechanics": ["walk"],
                 "difficulty": 1, "requires_key": True, "move_budget": 3},
                {"id": "b", "grid": ["K.S", "G.#"], "mechanics": ["walk"],
                 "difficulty": 7, "requires_key": True, "move_budget": 2},
            ],
            "policy": {"max_difficulty_step": 2, "min_mechanic_sets": 2, "max_layout_similarity": 1},
        }
        report = audit_gameplay.audit(payload)
        self.assertEqual(report["levels"][0]["shortest_solution_moves"], 3)
        self.assertEqual({issue["check"] for issue in report["issues"]},
                         {"unwinnable", "difficulty_jump", "repeated_layout", "unused_mechanic",
                          "low_mechanic_variety"})
        self.assertIsNone(audit_gameplay.reachable(["S#G"], (0, 0), True))

    def test_graph_and_timing_gameplay_audit(self):
        rules = {"verb": "tap", "feedback": "flash", "failure": "miss", "recovery": "retry"}
        payload = {
            "mechanics": {"observe": rules, "tap": rules},
            "levels": [
                {
                    "id": "g1",
                    "mechanics": ["observe"],
                    "difficulty": 1,
                    "requires_key": True,
                    "move_budget": 3,
                    "graph": {
                        "nodes": ["start", "clue", "goal"],
                        "start": "start",
                        "key_node": "clue",
                        "goal": "goal",
                        "edges": [["start", "clue"], ["clue", "goal"]],
                    },
                    "timing": {"reaction_window_ms": 2000, "min_gap_ms": 800, "concurrent_max": 2},
                },
                {
                    "id": "g2",
                    "mechanics": ["observe", "tap"],
                    "difficulty": 2,
                    "timing": {"reaction_window_ms": 1200, "min_gap_ms": 500, "concurrent_max": 3},
                },
            ],
            "policy": {
                "max_difficulty_step": 2,
                "min_mechanic_sets": 2,
                "min_reaction_window_ms": 1500,
                "min_event_gap_ms": 600,
                "max_concurrent_events": 2,
            },
        }
        report = audit_gameplay.audit(payload)
        self.assertEqual(report["levels"][0]["shortest_solution_moves"], 2)
        self.assertIsNone(report["levels"][1]["shortest_solution_moves"])
        timing_issues = [item for item in report["issues"] if item["check"] == "unfair_timing"]
        self.assertEqual(len(timing_issues), 3)
        self.assertEqual({item["reason"] for item in timing_issues},
                         {"reaction_window_below_minimum", "event_gap_below_minimum", "concurrent_events_exceed_max"})

    def test_experience_provenance_and_missing(self):
        criterion = {"threshold": 0.75, "min_samples": 8, "method": "coded after test", "population": "novice"}
        observation = {"source": "synthetic", "value": 1, "sample_size": 1000, "reference": "scenario-A"}
        data = {"plan": {"target_emotion_rate": criterion, "meaningful_choice_rate": criterion},
                "observations": {"target_emotion_rate": observation}}
        results = evaluate_experience.evaluate(data)
        self.assertEqual(results["target_emotion_rate"]["status"], "synthetic_only")
        self.assertEqual(results["meaningful_choice_rate"]["status"], "missing")
        observation.update(source="human_playtest", sample_size=4)
        self.assertEqual(evaluate_experience.evaluate(data)["target_emotion_rate"]["status"], "insufficient")
        observation.update(sample_size=8, value=0.6)
        self.assertEqual(evaluate_experience.evaluate(data)["target_emotion_rate"]["status"], "missed")
        observation["value"] = 0.8
        self.assertEqual(evaluate_experience.evaluate(data)["target_emotion_rate"]["status"], "met")


class EvidenceTests(unittest.TestCase):
    def test_finite_types_and_missing_telemetry(self):
        data = copy.deepcopy(audit_telemetry.DEMO_TELEMETRY)
        data["baseline_session_minutes"] = float("nan")
        data["ads"]["mid_gameplay_interstitial_count"] = True
        data["economy"]["fake_resetting_timers"] = "false"
        del data["economy"]["restorable_purchases"]
        errors, missing = validate(data)
        self.assertEqual(len(errors), 3)
        self.assertIn("economy.restorable_purchases", missing)

    def test_synthetic_audit_and_partial_signals(self):
        def run(data):
            with tempfile.TemporaryDirectory() as scratch:
                path = pathlib.Path(scratch) / "input.json"
                path.write_text(json.dumps(data))
                result = subprocess.run([sys.executable, str(SCRIPTS / "audit_telemetry.py"),
                                         "--input", str(path), "--format", "json"], capture_output=True, check=False)
                return result.returncode, json.loads(result.stdout)
        status, report = run({"ads": {"mid_gameplay_interstitial_count": 1}})
        self.assertEqual(status, 1)
        self.assertEqual(report["provenance"]["kind"], "unknown")
        self.assertIsNone(report["stage_3_neurobiological_risk"])
        self.assertIn("match_history", report["missing"])
        status, report = run(audit_telemetry.DEMO_TELEMETRY)
        self.assertEqual(status, 1)
        self.assertEqual(report["provenance"]["kind"], "synthetic")

    def test_screen_controls(self):
        data = {"match_history": ["W", "L", "W"] * 20, "damage_multiplier_observed": 1.3,
                "economy": {"paid_random_rewards": False, "odds_disclosed": False},
                "ads": {"avg_interstitial_interval_seconds": 2, "interstitial_interval_samples": 1}}
        result = audit_telemetry.stage2_classify(data, audit_telemetry.stage1_diagnose(data))
        self.assertFalse(result["EOMM_detected"])
        self.assertFalse(result["DDA_detected"])
        self.assertFalse(result["DARK_PATTERN_detected"])
        self.assertEqual(rebound_test(["L", "L", "W"] * 100)["status"], "signal")

    def test_synthetic_pairing_uses_global_minimum_cost(self):
        costs = [[1.0, 2.0, 9.0], [2.0, 9.0, 9.0], [9.0, 3.0, 1.0]]
        pairs = simulate_eomm_dda.minimum_cost_assignment(costs)
        self.assertEqual(pairs, [(0, 1), (1, 0), (2, 2)])
        self.assertEqual(simulate_eomm_dda.minimum_cost_assignment([[1.0, 1.0], [1.0, 1.0]]),
                         [(0, 0), (1, 1)])

    def test_simulation_replicates_and_degenerate_statistics(self):
        args = (20, 5, 8, 42, 10)
        first = simulate_eomm_dda.run_experiment(*args)
        self.assertEqual(first, simulate_eomm_dda.run_experiment(*args))
        self.assertEqual(len({item["seed"] for item in first["replicates"]}), 10)
        self.assertEqual(first["total_per_policy"], 200)
        self.assertIsNone(first["welch_p"])
        self.assertIsNone(simulate_eomm_dda.compute_statistics([0, 0], [0, 0])["cohens_d"])


class InstallationAndBenchmarkTests(unittest.TestCase):
    def test_host_targets_and_probe(self):
        for host, expected in (("codex", ".agents"), ("claude-code", ".claude"), ("antigravity", ".agents")):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as scratch:
                project = pathlib.Path(scratch).resolve()
                args = [sys.executable, str(SCRIPTS / "install_skill.py"), host]
                options = ["--project", str(project)]
                installed = subprocess.run(args + ["install"] + options, capture_output=True, check=True)
                dest = pathlib.Path(json.loads(installed.stdout)["path"])
                self.assertEqual(dest.relative_to(project).parts[0], expected)
                prepared = subprocess.run(args + ["prepare"] + options, capture_output=True, check=True)
                command = json.loads(prepared.stdout)["positive_prompt"]
                self.assertTrue(command.startswith(install_skill.HOSTS[host][1]))
                probe = dest / install_skill.PROBE
                self.assertTrue(install_skill.proof(probe, host, probe.read_text(), "CONTROL_OK"))
                self.assertFalse(install_skill.proof(probe, host, probe.read_text(), probe.read_text()))
                self.assertTrue(install_skill.matching(dest))
                (dest / "SKILL.md").write_text("changed")
                self.assertFalse(install_skill.matching(dest))
                with self.assertRaises(ValueError):
                    install_skill.install(dest)
                subprocess.run(args + ["upgrade"] + options, capture_output=True, check=True)
                self.assertTrue(install_skill.matching(dest))

    def test_global_plugin_install_check_and_upgrade(self):
        with tempfile.TemporaryDirectory() as scratch:
            plugin_dir = pathlib.Path(scratch).resolve() / "beyin-bedava"
            plugin_dir.mkdir()
            (plugin_dir / ".git").mkdir()
            (plugin_dir / ".git/HEAD").write_text("ref: refs/heads/main\n")
            base = [sys.executable, str(SCRIPTS / "install_skill.py"), "antigravity"]
            opts = ["--global-plugin", "--plugin-dir", str(plugin_dir)]
            subprocess.run(base + ["install"] + opts, capture_output=True, check=True)
            subprocess.run(base + ["check"] + opts, capture_output=True, check=True)
            (plugin_dir / "plugin.json").write_text('{"version":"0.0.0"}')
            (plugin_dir / "skills/beyin-bedava/stale.md").write_text("stale")
            failed_check = subprocess.run(base + ["check"] + opts, capture_output=True)
            self.assertEqual(failed_check.returncode, 2)
            subprocess.run(base + ["upgrade"] + opts, capture_output=True, check=True)
            subprocess.run(base + ["check"] + opts, capture_output=True, check=True)
            self.assertFalse((plugin_dir / "skills/beyin-bedava/stale.md").exists())
            self.assertTrue((plugin_dir / ".git/HEAD").is_file())

    def test_benchmark_executes_bounded_rules_and_rejects_calls(self):
        tasks = json.loads((ROOT / "benchmarks/tasks.json").read_text())
        task = tasks[0]
        answer = {"expression": "0 if action == 2 else charge if opened else min(3, charge + 1)"
                                " if action == 0 else 0 if charge == 3 else charge"}
        self.assertEqual(benchmark.grade(json.dumps(answer), task)["task_completion"], 1)
        answer["expression"] = "__import__('os').system('anything')"
        self.assertEqual(benchmark.grade(json.dumps(answer), task)["error_rate"], 1)
        answer["expression"] = "1 // charge"
        self.assertGreater(benchmark.grade(json.dumps(answer), task)["error_rate"], 0)

        solutions = {
            "pulse-gate": "0 if action == 2 else charge if opened else min(3, charge + 1) if action == 0 else 0 if charge == 3 else charge",
            "optional-assist": "min(6, (failures - 1) * 2) if opt_in == 1 and competitive == 0 and failures >= 2 else 0",
            "practice-medals": "0 if practice == 1 else min(7, max(0, successes * 2 - hints))",
            "fair-window-scoring": "-40 if is_culprit == 0 else 0 if elapsed_cs > 200 else min(130, 100 + combo * 10)",
            "bounded-pity-drop": "1 if paid_random == 1 and pulls_since_rare >= pity_cap - 1 else 0",
        }
        self.assertEqual(len(tasks), len(solutions))
        for item in tasks:
            with self.subTest(task=item["id"]):
                result = benchmark.grade(json.dumps({"expression": solutions[item["id"]]}), item)
                self.assertEqual(result["task_completion"], 1.0)
                self.assertEqual(result["error_rate"], 0.0)

    def test_benchmark_schedule_balances_which_condition_runs_first(self):
        tasks = [{"id": "a"}, {"id": "b"}]
        first = benchmark.paired_schedule(tasks, 4, 42)
        self.assertEqual(first, benchmark.paired_schedule(tasks, 4, 42))
        for task in tasks:
            self.assertEqual(sum(item[2][0] == "off" for item in first if item[0] == task), 2)

    def test_benchmark_reports_provider_failure_separately(self):
        failed = {"status": "provider_error", "seconds": 1}
        complete = {"status": "completed", "seconds": 3, "task_completion": 1, "total_tokens": 100}
        on_complete = {"status": "completed", "seconds": 4, "task_completion": 1, "total_tokens": 400}
        summary = benchmark.aggregate([{"on": failed, "off": complete}, {"on": on_complete, "off": complete}])
        self.assertEqual(summary["completed_pairs"], 1)
        self.assertEqual(summary["provider_error_rate"], {"on": 0.5, "off": 0})
        self.assertEqual(summary["metrics"]["seconds"]["off_mean"], 3)
        self.assertIsNone(summary["metrics"]["input_tokens"])
        self.assertEqual(summary["token_overhead_ratio"], 4.0)


if __name__ == "__main__":
    unittest.main()
