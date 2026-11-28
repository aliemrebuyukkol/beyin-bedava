from contextlib import closing
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/beyin-bedava"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import detect_game_project as detector
from install_skill import GENERATED
import plan_game_integration as integration
from task_ledger import Ledger


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = integration.read_json(integration.CATALOG_PATH)
        cls.schema = integration.read_json(integration.SCHEMA_PATH)

    def plan(self, game, focus=("build",), notes=(), explicit=False):
        return integration.create_plan(game, "Check gate recovery", focus, "baseline",
                                       explicit, list(notes), self.catalog, self.schema)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "plan_game_integration.py"), *map(str, args)],
                              text=True, capture_output=True, timeout=20)

    def test_all_skill_references_are_routable(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)
        paths = [item["path"] for item in self.catalog["modules"]]
        expected = {path.relative_to(SKILL).as_posix() for path in SKILL.rglob("*.md")
                    if not GENERATED.intersection(path.relative_to(SKILL).parts) and path.name != "SKILL.md"}
        self.assertEqual(set(paths), expected)
        self.assertEqual(len(paths), len(set(paths)))
        focuses = set(self.schema["$defs"]["focus"]["enum"])
        for item in self.catalog["modules"]:
            self.assertTrue(set(item["focus"]) <= focuses | {"core"})

    def test_sources_and_modules_are_scoped_and_generate_ledger(self):
        notes = integration.read_json(SKILL / "examples/integration-research.json")
        plan = self.plan(SKILL / "adapters/godot", ["build", "telemetry"], notes)
        paths = {module["path"] for module in plan["modules"]}
        self.assertIn("orchestration/telemetry.md", paths)
        self.assertNotIn("references/ads-and-iap-architecture.md", paths)
        self.assertNotIn("adapters/swift/README.md", paths)
        self.assertEqual(plan["research"]["engine"]["sources"], notes)
        self.assertEqual(plan["research"]["engine"]["status"], "recorded")
        self.assertEqual(plan["research"]["telemetry"]["status"], "unresearched")
        self.assertEqual(plan["checks"][0]["id"], "pulse_flow")
        result = self.run_cli("plan", SKILL / "adapters/godot", "--goal", "Assign a file",
                              "--own", "wire", "main.gd")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan_with_files = json.loads(result.stdout)
        self.assertEqual(next(task for task in plan_with_files["tasks"] if task["id"] == "wire")["files"], ["main.gd"])
        self.assertEqual(plan_with_files["plan_id"], integration.digest(plan_with_files))
        duplicate = self.run_cli("plan", SKILL / "adapters/godot", "--goal", "Assign a file",
                                 "--own", "inspect", "main.gd", "--own", "wire", "main.gd")
        self.assertEqual(duplicate.returncode, 2)
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory) / "state.db")
            with closing(ledger.db):
                ledger.init(plan)
                self.assertEqual(ledger.claim("beyin-bedava", 30)["task"], "inspect")

    def test_non_game_requires_explicit_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            with self.assertRaisesRegex(ValueError, "could not be identified"):
                self.plan(workspace)
            plan = self.plan(workspace, explicit=True)
            self.assertEqual(plan["project"]["engine"], "unknown")
            self.assertEqual(plan["checks"], [])
            self.assertEqual(list(workspace.iterdir()), [])
            sample = {"version": 1, "plan_id": plan["plan_id"], "revision": "run",
                      "source": "runtime", "checks": []}
            self.assertEqual(integration.verify(plan, sample, "run", self.schema)["status"], "insufficient")

    def test_terminal_game_produces_real_evidence_and_rejects_wrong_revision(self):
        game = SKILL / "adapters/terminal"
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            result = self.run_cli("plan", game, "--goal", "Verify the gate", "--output", plan_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual(plan["project"]["basis"], "declared_manifest")
            self.assertIsNone(plan["project"]["detector_engine"])
            self.assertNotEqual(self.run_cli("plan", game, "--goal", "Second run", "--output", plan_path).returncode, 0)
            run = subprocess.run([sys.executable, str(game / "pulse_gate.py"), "--plan", str(plan_path),
                                  "--revision", "run-2"], text=True, capture_output=True, check=True, timeout=10)
            actual = json.loads(run.stdout)
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(run.stdout, encoding="utf-8")
            self.assertEqual(self.run_cli("verify", plan_path, evidence_path, "--revision", "run-2").returncode, 0)
            self.assertEqual(self.run_cli("verify", plan_path, evidence_path, "--revision", "run-1").returncode, 2)

            synthetic = copy.deepcopy(actual)
            synthetic["source"] = "synthetic"
            self.assertEqual(integration.verify(plan, synthetic, "run-2", self.schema)["status"], "insufficient")
            tampered = {**plan, "goal": "A different acceptance scope"}
            with self.assertRaisesRegex(ValueError, "invalid integration plan"):
                integration.verify(tampered, actual, "run-2", self.schema)
            wrong = copy.deepcopy(actual)
            wrong["checks"][0]["observed"]["blocked"] = 1
            self.assertEqual(integration.verify(plan, wrong, "run-2", self.schema)["status"], "failed")
            omitted = copy.deepcopy(actual)
            omitted["checks"] = []
            self.assertEqual(integration.verify(plan, omitted, "run-2", self.schema)["status"], "insufficient")

            wrong["checks"][0]["id"] = "unknown"
            with self.assertRaisesRegex(ValueError, "out-of-scope"):
                integration.verify(plan, wrong, "run-2", self.schema)

    @unittest.skipUnless(shutil.which("godot"), "Godot engine unavailable")
    def test_godot_scene_controls_produce_real_evidence(self):
        game = SKILL / "adapters/godot"
        plan = self.plan(game)
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = subprocess.run(
                ["godot", "--headless", "--path", str(game), "--", "--self-test",
                 f"--evidence-plan={plan_path}", "--revision=godot-run"], capture_output=True,
                text=True, timeout=20, env={**os.environ, "XDG_CACHE_HOME": directory, "XDG_DATA_HOME": directory},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            line = next(line for line in result.stdout.splitlines() if line.startswith("BEYIN_EVIDENCE "))
            evidence = json.loads(line.removeprefix("BEYIN_EVIDENCE "))
            self.assertEqual(integration.verify(plan, evidence, "godot-run", self.schema)["status"], "passed")

    def test_duplicate_fields_and_nonfinite_numbers_are_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for payload in ['{"a": 1, "a": 2}', '{"value":NaN}', '{"value":1e999}']:
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    path.write_text(payload, encoding="utf-8")
                    integration.read_json(path)

    def test_detector_distinguishes_engines_and_skips_symlinks(self):
        cases = [
            ("project.yyp", "", "gamemaker"), ("world.rbxlx", "", "roblox"),
            ("game/script.rpy", "label start:", "renpy"), ("Game.rmmzproject", "", "rpg_maker"),
            ("Cargo.toml", '[dependencies]\nmacroquad = "0.4"\n', "macroquad"),
            ("pyproject.toml", '[project]\ndependencies = ["arcade>=3"]\n', "arcade"),
            ("package.json", '{"dependencies":{"@babylonjs/core":"1"}}', "web_babylon"),
        ]
        for name, data, expected in cases:
            with self.subTest(engine=expected), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                marker = workspace / name
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text(data, encoding="utf-8")
                self.assertEqual(detector.detect_engine(workspace, detector._collect_files(workspace))[1], expected)
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "pyproject.toml").write_text('[project]\ndependencies = ["not-arcade"]\n')
            self.assertFalse(detector.detect_engine(workspace, detector._collect_files(workspace))[0])
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            outside = workspace / "external"
            outside.mkdir()
            (outside / "project.godot").touch()
            scanned = workspace / "scanned"
            scanned.mkdir()
            try:
                (scanned / "project.godot").symlink_to(outside / "project.godot")
            except OSError:
                return
            self.assertFalse(detector.detect_engine(scanned, detector._collect_files(scanned))[0])

    def test_duplicate_check_ids_are_rejected_before_planning(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = integration.read_json(SKILL / "adapters/terminal" / integration.MANIFEST_NAME)
            source["checks"] *= 2
            (workspace / integration.MANIFEST_NAME).write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate check"):
                self.plan(workspace)

    def test_threshold_comparators_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            manifest = {
                "version": 1,
                "game": {"name": "Latency Bench", "engine": "terminal-lite"},
                "checks": [
                    {
                        "id": "frame_budget",
                        "focus": "build",
                        "description": "Verify p95 latency, drop rate, fps window, and calibrated ratio.",
                        "expect": {
                            "p95_ms": {"lte": 33.3},
                            "missed_rate": {"lt": 0.05},
                            "fps": {"between": [58, 62]},
                            "scale": {"approx": 1.0, "tol": 0.02},
                            "stable": True,
                        },
                    }
                ],
            }
            (workspace / integration.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
            plan = self.plan(workspace)
            passing = {
                "version": 1, "plan_id": plan["plan_id"], "revision": "r1", "source": "runtime",
                "checks": [{"id": "frame_budget", "artifact": "trace.json", "observed": {
                    "p95_ms": 33.3, "missed_rate": 0.04, "fps": 60, "scale": 1.01, "stable": True,
                }}],
            }
            self.assertEqual(integration.verify(plan, passing, "r1", self.schema)["status"], "passed")

            boundary_fail = copy.deepcopy(passing)
            boundary_fail["checks"][0]["observed"]["missed_rate"] = 0.05
            boundary_fail["checks"][0]["observed"]["fps"] = True
            failed = integration.verify(plan, boundary_fail, "r1", self.schema)
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(failed["checks"]["frame_budget"]["mismatches"], ["fps", "missed_rate"])

            bad_manifest = copy.deepcopy(manifest)
            bad_manifest["checks"][0]["expect"]["fps"] = {"between": [5, 2]}
            (workspace / integration.MANIFEST_NAME).write_text(json.dumps(bad_manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "min <= max"):
                self.plan(workspace)

    def test_branch_agents_all_capabilities_new_project_and_autopilot(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "new_game"
            workspace.mkdir()
            result = self.run_cli(
                "plan", workspace,
                "--goal", "Create new game with all capabilities",
                "--all-capabilities", "--branch-agents", "--new-project",
                "--own", "wire", "src/main.py",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual(plan["project"]["basis"], "new_project_intent")
            self.assertEqual(set(plan["focus"]), set(self.schema["$defs"]["focus"]["enum"]))
            task_ids = [t["id"] for t in plan["tasks"]]
            self.assertEqual(
                task_ids,
                [
                    "inspect",
                    "research",
                    "branch_dna_mechanics",
                    "branch_progression_economy",
                    "branch_feel_ui",
                    "branch_monetization_gate",
                    "wire",
                    "branch_capability_audits",
                    "verify",
                    "completion_gate",
                ],
            )
            self.assertEqual(len(plan["checklist"]), len(plan["tasks"]))
            self.assertEqual(plan["monetization_gate"]["agent"], "monetization-gate-agent")
            self.assertEqual(plan["monetization_gate"]["choice"], "ask")
            self.assertTrue(plan["monetization_gate"]["requires_user_prompt"])

            db_path = Path(directory) / "autopilot.sqlite"
            auto = self.run_cli(
                "autopilot", workspace,
                "--goal", "Autopilot full completion",
                "--new-project", "--monetization-choice", "both",
                "--db", db_path, "--max-cycles", "2",
            )
            self.assertEqual(auto.returncode, 0, auto.stderr)
            payload = json.loads(auto.stdout)
            self.assertEqual(payload["status"], "completed")
            self.assertEqual(payload["monetization_gate"]["choice"], "both")
            self.assertTrue(payload["monetization_gate"]["ads_enabled"])
            self.assertTrue(payload["monetization_gate"]["paywall_enabled"])
            self.assertTrue(payload["completion"]["complete"])
            self.assertEqual(payload["completion"]["completion_pct"], 100.0)
            self.assertEqual(payload["completion"]["incomplete_count"], 0)


if __name__ == "__main__":
    unittest.main()
