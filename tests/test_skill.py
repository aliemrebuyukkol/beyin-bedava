import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "beyin-bedava"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import detect_game_project as detector
import audit_telemetry as audit
import install_skill as installer
import simulate_eomm_dda as sim

class SkillTests(unittest.TestCase):
    def test_config_safe_and_schema_valid(self):
        schema = json.loads((SKILL / "resources/beyin-bedava-config.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        config = detector.build_recommended_config("other", "swift_spritekit")
        jsonschema.validate(config, schema)
        release = json.loads((ROOT / "plugin.json").read_text())["version"]
        self.assertEqual(config["schemaVersion"], release)
        self.assertEqual(schema["properties"]["schemaVersion"]["default"], release)
        self.assertEqual(installer.VERSION, release)
        for version in ("2.0.0", "2.1.0", "3.0.0"):
            jsonschema.validate({**config, "schemaVersion": version}, schema)
        minimal = detector.build_minimal_config("puzzle_casual")
        jsonschema.validate(minimal, schema)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({**minimal, "enabledModules": ["dda"]}, schema)
        self.assertEqual(config["matchmaking"]["mode"], "disabled")
        self.assertFalse(config["dda"]["enabled"])
        self.assertFalse(config["adPlacements"]["enabled"])
        self.assertFalse(config["purchaseScreens"]["enabled"])
        config["matchmaking"]["weights"]["gamma_monetization"] = 0.1
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_swift_and_non_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            file = root / "Game.swift"
            file.write_text("import SwiftUI\nstruct ViewModel {}")
            self.assertFalse(detector.detect_engine(root, [file])[0])
            file.write_text("import SpriteKit\nclass Game: SKScene {}")
            self.assertEqual(detector.detect_engine(root, [file])[1], "swift_spritekit")
            file.write_text("import RealityKit\nclass GameState {}")
            self.assertEqual(detector.detect_engine(root, [file])[1], "swift_realitykit")

    def test_multi_engine_skip_dirs_and_minimal_emit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Game2D.swift").write_text("import SpriteKit\nclass MainScene: SKScene {}")
            (root / "Proto3D.swift").write_text("import RealityKit\nclass GameState {}")
            (root / "TestResults").mkdir()
            (root / "TestResults/report.json").write_text('{"store": true, "gacha": 1}')
            (root / "App.xcodeproj").mkdir()
            (root / "App.xcodeproj/project.pbxproj").write_text("matchmaking")
            (root / "Localization").mkdir()
            (root / "Localization/en.json").write_text('{"deck": "card", "mana_cost": 1}')
            files = detector._collect_files(root)
            is_game, primary, all_engines, langs, _ = detector.detect_all_engines(root, files)
            self.assertTrue(is_game)
            self.assertEqual(primary, "swift_spritekit")
            self.assertEqual(all_engines, ["swift_spritekit", "swift_realitykit"])
            self.assertEqual(langs, ["swift"])
            genre, _scores, systems, risks = detector.infer_genre_and_systems(root, files)
            self.assertEqual(genre, "other")
            self.assertEqual(systems["economy_or_iap"], [])
            self.assertEqual(risks, {})
            out = root / "min-config.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPTS / "detect_game_project.py"), str(root),
                 "--emit-config", str(out), "--minimal"],
                capture_output=True, check=True,
            )
            payload = json.loads(run.stdout)
            self.assertEqual(payload["detected_engines"], ["swift_spritekit", "swift_realitykit"])
            emitted = json.loads(out.read_text())
            self.assertEqual(emitted, {"schemaVersion": "3.1.0", "gameGenre": "other", "enabledModules": []})

    def test_flame(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            manifest = root / "pubspec.yaml"
            manifest.write_text("dependencies:\n  flame: any\n")
            code = root / "game.dart"
            code.write_text("class MyGame extends FlameGame {}")
            self.assertEqual(detector.detect_engine(root, [manifest, code])[1], "flutter_flame")

    def test_small_sample_not_detected(self):
        data = {"match_history": ["L", "L", "W"]}
        result = audit.stage2_classify(data, audit.stage1_diagnose(data))
        self.assertFalse(result["EOMM_detected"])
        self.assertEqual(result["EOMM_evidence_status"], "insufficient")

    def test_empty_audit_is_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "input.json"
            path.write_text("{}")
            run = subprocess.run([sys.executable, str(SCRIPTS / "audit_telemetry.py"), "--input", str(path)], capture_output=True)
            self.assertEqual(run.returncode, 2)

    def test_demo_flags_policy_violation(self):
        run = subprocess.run([sys.executable, str(SCRIPTS / "audit_telemetry.py"), "--demo", "--format", "json"], capture_output=True)
        self.assertEqual(run.returncode, 1, run.stderr.decode())
        self.assertTrue(json.loads(run.stdout)["stage_2_algorithmic_classification"]["DARK_PATTERN_detected"])

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "project.godot").touch()
            config = root / "existing.json"
            config.write_text("original")
            run = subprocess.run([sys.executable, str(SCRIPTS / "detect_game_project.py"), str(root), "--emit-config", str(config)], capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(config.read_text(), "original")

    def test_odd_pool_no_duplicate_and_bye(self):
        players = [sim.SyntheticPlayer(i, float(i)) for i in [3, 4, 2, 1, 0]]
        pairs = sim.pair_pool(players, "sbmm")
        ids = [p.player_id for pair in pairs for p in pair]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(0, ids)
        self.assertIn(4, ids)

    def test_simulation_limits(self):
        run = subprocess.run([sys.executable, str(SCRIPTS / "simulate_eomm_dda.py"), "--max-hitbox", "2"], capture_output=True)
        self.assertNotEqual(run.returncode, 0)

    def test_skill_references_exist(self):
        import re
        for path in re.findall(r"\]\(([^)]+\.md)\)", (SKILL / "SKILL.md").read_text()):
            self.assertTrue((SKILL / path).is_file(), path)

if __name__ == "__main__":
    unittest.main()
