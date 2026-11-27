#!/usr/bin/env python3
"""Autonomous Game Project Detector & Beyin-Bedava Configurator.

Inspects any workspace directory to determine:
  1. Whether it is a game project and which engine/language it uses
  2. Inferred game genre
  3. Existing matchmaking, DDA, economy, ad placement, IAP/store, and transparency modules
  4. Static dark-pattern / algorithmic risk signals
  5. Genre-tailored `beyin-bedava-config.json` and concrete autonomous integration steps
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

SKIP_DIRS: Set[str] = {
    ".git",
    ".agents",
    ".beyin-bedava",
    ".claude",
    ".codex",
    ".godot",
    ".build",
    ".dart_tool",
    ".import",
    ".next",
    ".venv",
    "__pycache__",
    "Binaries",
    "DerivedDataCache",
    "Intermediate",
    "Library",
    "Logs",
    "Obj",
    "Temp",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
}

TEXT_EXTENSIONS: Set[str] = {
    ".swift",
    ".dart",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".gd",
    ".tscn",
    ".tres",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".py",
    ".rs",
    ".lua",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".html",
    ".css",
}

SKIP_FILES: Set[str] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
}

GENRE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "fps": ("bullet", "headshot", "ammo", "recoil", "crosshair", "raycast", "hitscan", "shooter", "fps"),
    "action_platformer": ("platformer", "coyote", "jump_buffer", "wall_jump", "dash", "hurtbox", "iframe", "metroidvania", "characterbody2d", "velocity"),
    "rpg_roguelike": ("dungeon", "roguelike", "inventory", "experience_points", "level_up", "loot", "quest", "rpg", "mana", "crit_chance"),
    "puzzle_casual": ("match3", "puzzle", "tile", "swap", "grid", "pair", "card_flip", "eslestirme", "memory", "combo", "board"),
    "strategy_card": ("deck", "card", "mana_cost", "turn_based", "draw_pile", "gacha", "summon", "tower_defense", "strategy"),
    "racing_sports": ("lap", "drift", "throttle", "brake", "racing", "checkpoint", "slipstream", "stadium", "scoreboard"),
}

GENRE_REGEXES: Dict[str, List[re.Pattern[str]]] = {
    genre: [re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in kws]
    for genre, kws in GENRE_KEYWORDS.items()
}

STATIC_RISK_PATTERNS: List[Tuple[str, str]] = [
    ("one_click_or_no_confirm", r"(one_click|instant_buy|skip_confirm|auto_purchase)"),
    ("forced_interstitial_risk", r"(show_interstitial|showInterstitial|interstitialAd)"),
    ("rewarded_revive_coupling", r"(revive_ad|watch_ad_to_revive|ad_revive)"),
    ("dual_currency_tokens", r"(hard_currency|gems|crystals|diamonds)\b"),
    ("loot_or_gacha_rng", r"(loot_box|lootbox|gacha|drop_rate|rarity_roll)"),
    ("fomo_countdown_or_streak", r"(daily_streak|streak_reset|countdown_timer|limited_offer|energy_refill)"),
    ("hidden_dda_multipliers", r"(hitbox_scale|bullet_magnet|damage_multiplier|rubber_band)"),
]


def _read_text_safe(path: Path, max_bytes: int = 120_000) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _collect_files(root: Path, max_files: int = 1200) -> List[Path]:
    collected: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        directory = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not (directory / d).is_symlink())
        for fname in sorted(filenames):
            path = directory / fname
            if path.is_symlink() or not path.is_file():
                continue
            collected.append(path)
            if len(collected) >= max_files:
                return collected
    return collected


def detect_engine(root: Path, files: List[Path]) -> Tuple[bool, str, List[str], List[str]]:
    evidence: List[str] = []
    languages: Set[str] = set()
    rel_names = {f.relative_to(root).as_posix() for f in files}
    basenames = {f.name for f in files}

    if "project.godot" in basenames:
        evidence.append("Found project.godot")
        engine = "godot"
        if not any(f.suffix == ".cs" for f in files):
            languages.add("gdscript")
    elif any(r == "ProjectSettings/ProjectVersion.txt" or r.endswith("/ProjectSettings/ProjectVersion.txt")
             for r in rel_names) or any(f.suffix == ".unity" for f in files):
        evidence.append("Found Unity ProjectSettings or .unity scene")
        engine = "unity"
        languages.add("csharp")
    elif any(f.suffix == ".uproject" for f in files):
        evidence.append("Found Unreal .uproject file")
        engine = "unreal"
        languages.add("cpp")
    elif any(f.suffix == ".yyp" for f in files):
        evidence.append("Found a GameMaker .yyp project")
        engine = "gamemaker"
        languages.add("gml")
    elif any(f.suffix in {".rbxl", ".rbxlx"} for f in files):
        evidence.append("Found a Roblox place file")
        engine = "roblox"
        languages.add("luau")
    elif any(f.suffix in {".rpgproject", ".rmmzproject"} for f in files):
        evidence.append("Found an RPG Maker MV/MZ project marker")
        engine = "rpg_maker"
    elif any(f.suffix == ".rpy" and "game" in f.relative_to(root).parts[:-1] for f in files):
        evidence.append("Found a Ren'Py script in a game directory")
        engine = "renpy"
    elif "conf.lua" in basenames and any(f.name == "main.lua" for f in files):
        evidence.append("Found LÖVE2D conf.lua + main.lua")
        engine = "love2d"
        languages.add("lua")
    else:
        engine = "non_game"

    try:
        package = json.loads(_read_text_safe(root / "package.json") or "{}")
    except ValueError:
        package = {}
    web_engines = {
        "phaser": "web_phaser", "pixi.js": "web_pixijs", "three": "web_threejs",
        "babylon": "web_babylon", "@babylonjs/core": "web_babylon",
        "kaboom": "web_canvas", "excalibur": "web_canvas", "playcanvas": "web_playcanvas",
    }
    if isinstance(package, dict):
        for field in ("dependencies", "devDependencies", "peerDependencies"):
            dependencies = package.get(field)
            if isinstance(dependencies, dict):
                for dependency in sorted(dependencies.keys() & web_engines.keys()):
                    evidence.append(f"package.json declares {dependency} in {field}")
                    if engine == "non_game":
                        engine = web_engines[dependency]

    cargo_text = _read_text_safe(root / "Cargo.toml").lower()
    for dependency in ("bevy", "macroquad", "ggez"):
        if re.search(rf"(?m)^\s*(?:{dependency}\s*=|\[[^\]\n]*dependencies\.{dependency}\])", cargo_text):
            evidence.append(f"Cargo.toml declares {dependency}")
            if engine == "non_game":
                engine = dependency
            languages.add("rust")

    for py_manifest in ("pyproject.toml", "requirements.txt"):
        source = _read_text_safe(root / py_manifest).lower()
        for package_name in ("pygame", "arcade", "ursina"):
            prefix = r"(?m)^[ 	]*"
            if py_manifest == "pyproject.toml":
                # PEP 621 dependencies and Poetry key/value declarations.
                prefix = r"(?m)(?:^[ 	]*|^[ 	]*dependencies[ 	]*=[ 	]*\[(?:[^\n]*,)?)[ 	]*"
            if re.search(rf"""{prefix}(?:"|')?{package_name}(?:-ce)?(?=["'\s<>=~!;\[\n]|$)""", source):
                evidence.append(f"{py_manifest} declares {package_name}")
                if engine == "non_game":
                    engine = package_name
                languages.add("python")

    # Native game evidence: framework plus gameplay marker (not just a 3D viewer).
    if engine == "non_game":
        for f in files:
            if f.suffix != ".swift":
                continue
            source = _read_text_safe(f)
            if re.search(r"\b(SKScene|SKPhysicsContactDelegate|SKAction)\b", source) and re.search(r"\bimport\s+SpriteKit\b", source):
                engine = "swift_spritekit"
            elif re.search(r"\bimport\s+RealityKit\b", source) and re.search(r"\b(gameLoop|GameSystem|GameState|gameOver|PlayerController|gameState)\b", source):
                engine = "swift_realitykit"
            elif re.search(r"\bimport\s+SceneKit\b", source) and re.search(r"\b(SCNPhysicsContactDelegate|gameLoop|GameState|gameOver|gameState)\b", source):
                engine = "swift_scenekit"
            if engine != "non_game":
                evidence.append(f"Native game framework and gameplay evidence: {f.relative_to(root)}")
                break
    manifest = root / "pubspec.yaml"
    if engine == "non_game" and manifest.exists() and re.search(r"(?m)^\s+flame\s*:", _read_text_safe(manifest)):
        if any(f.suffix == ".dart" and re.search(r"\b(FlameGame|GameWidget)\b", _read_text_safe(f)) for f in files):
            engine = "flutter_flame"
            evidence.append("Flame dependency and game source")
    # Fallback heuristic for custom HTML5/Canvas/React/TS games
    ext_map = {
        ".swift": "swift",
        ".dart": "dart",
        ".gd": "gdscript",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".py": "python",
        ".rs": "rust",
        ".lua": "lua",
        ".luau": "luau",
        ".rpy": "renpy",
        ".gml": "gml",
    }
    game_loop_hits = 0
    for f in files:
        if f.name in SKIP_FILES:
            continue
        if f.suffix in ext_map:
            languages.add(ext_map[f.suffix])
        if f.suffix in TEXT_EXTENSIONS:
            txt = _read_text_safe(f).lower()
            if re.search(r"\b(requestanimationframe|gameloop|game_state|gameover|matchcard|phaser|pixi|new\s+game|oyun\b|oyunu)\b", txt) or "<canvas" in txt:
                game_loop_hits += 1

    if engine == "non_game" and game_loop_hits >= 2 and ("typescript" in languages or "javascript" in languages):
        engine = "web_canvas"
        evidence.append(f"Detected {game_loop_hits} files with game loop/state markers")

    is_game = engine != "non_game"
    return is_game, engine, sorted(languages), evidence


def infer_genre_and_systems(root: Path, files: List[Path]) -> Tuple[str, Dict[str, int], Dict[str, List[str]], Dict[str, List[str]]]:
    genre_scores: Dict[str, int] = {k: 0 for k in GENRE_KEYWORDS}
    detected_systems: Dict[str, List[str]] = {
        "beyin_bedava_config": [],
        "matchmaking_or_dda": [],
        "economy_or_iap": [],
        "ads": [],
        "transparency_or_wellbeing": [],
    }
    risk_signals: Dict[str, List[str]] = {}

    root_lower = root.name.lower()
    for genre, regexes in GENRE_REGEXES.items():
        for rx in regexes:
            if rx.search(root_lower):
                genre_scores[genre] += 2

    for f in files:
        if f.name in SKIP_FILES or f.suffix not in TEXT_EXTENSIONS:
            continue
        rel = f.relative_to(root).as_posix()
        txt = _read_text_safe(f)
        lower = txt.lower()

        if f.name == "beyin-bedava-config.json":
            detected_systems["beyin_bedava_config"].append(rel)

        for genre, regexes in GENRE_REGEXES.items():
            for rx in regexes:
                if rx.search(txt) or rx.search(rel):
                    genre_scores[genre] += 1

        if any(tok in lower for tok in ("matchmaking", "sbmm", "eomm", "elo", "dda", "difficulty")):
            detected_systems["matchmaking_or_dda"].append(rel)
        if any(tok in lower for tok in ("store", "shop", "iap", "purchase", "revenuecat", "storekit", "billing", "stripe", "currency", "coin")):
            detected_systems["economy_or_iap"].append(rel)
        if any(tok in lower for tok in ("admob", "rewarded", "interstitial", "banner", "applovin", "levelplay", "adsense", "poki", "crazygames")):
            detected_systems["ads"].append(rel)
        if any(tok in lower for tok in ("transparency", "grayscale", "two_loss", "two-loss", "cooling_off", "wellbeing", "beyin_bedava", "beyin-bedava")):
            detected_systems["transparency_or_wellbeing"].append(rel)

        for risk_name, pattern in STATIC_RISK_PATTERNS:
            if re.search(pattern, txt, flags=re.IGNORECASE):
                risk_signals.setdefault(risk_name, []).append(rel)

    best_genre = max(genre_scores.items(), key=lambda kv: kv[1])
    inferred = best_genre[0] if best_genre[1] >= 2 else "other"
    for k in detected_systems:
        detected_systems[k] = detected_systems[k][:15]
    for k in risk_signals:
        risk_signals[k] = risk_signals[k][:10]
    return inferred, genre_scores, detected_systems, risk_signals


def build_recommended_config(genre: str, engine: str) -> Dict[str, Any]:
    rewarded_by_genre: Dict[str, List[Dict[str, Any]]] = {
        "fps": [
            {"id": "post_match_double_coins", "surface": "match_summary", "rewardType": "coins", "rewardAmount": 100},
        ],
        "action_platformer": [
            {"id": "post_run_bonus_coins", "surface": "run_summary", "rewardType": "coins", "rewardAmount": 75},
        ],
        "rpg_roguelike": [
            {"id": "campfire_reroll", "surface": "campfire_modal", "rewardType": "reroll_token", "rewardAmount": 1},
        ],
        "puzzle_casual": [
            {"id": "optional_hint", "surface": "puzzle_hud", "rewardType": "hint", "rewardAmount": 1},
        ],
        "strategy_card": [
            {"id": "daily_shop_refresh", "surface": "store_header", "rewardType": "shop_refresh", "rewardAmount": 1},
        ],
        "racing_sports": [
            {"id": "podium_purse_double", "surface": "race_summary", "rewardType": "coins", "rewardAmount": 150},
        ],
        "other": [
            {"id": "post_round_bonus", "surface": "round_summary", "rewardType": "coins", "rewardAmount": 50},
        ],
    }
    ad_provider = "h5_sdk" if engine.startswith("web_") else "mock"
    iap_provider = "stripe_web" if engine.startswith("web_") else "mock"

    return {
        "schemaVersion": "2.1.0",
        "gameGenre": genre,
        "transparency": {
            "discloseMatchmaking": True,
            "discloseDDA": True,
            "discloseOdds": True,
            "discloseAdRules": True,
            "playerOptOutAllowed": True,
        },
        "matchmaking": {
            "mode": "disabled",
            "weights": {
                "alpha_latency": 0.35,
                "beta_skill": 0.55,
                "gamma_monetization": 0.0,
                "delta_social": 0.10,
            },
            "eommChurnWeights": {
                "consecutiveLoss3": 0.72,
                "consecutiveLoss2": 0.45,
                "alternatingWLW": 0.14,
                "consecutiveWin3": 0.28,
            },
            "maxConsecutiveLossesBeforeRelief": 2,
        },
        "dda": {
            "enabled": False,
            "struggleThreshold": 0.50,
            "maxHitboxMultiplier": 1.25,
            "maxBulletMagnetism": 0.25,
            "maxDamageMultiplier": 1.18,
            "criticalHpThreshold": 0.15,
            "criticalHpDampingRate": 3.0,
        },
        "economy": {
            "softCurrencyName": "coins",
            "hardCurrencyName": "none",
            "faucets": ["match_completion", "milestone_quest"],
            "sinks": ["cosmetics", "upgrades"],
            "preventBundlePriceMismatch": True,
            "showRealMoneyEquivalent": True,
            "hardPityThreshold": 20,
        },
        "adPlacements": {
            "enabled": False,
            "providerMode": "mock" if ad_provider != "mock" else "mock",
            "requireConsentBeforeInit": True,
            "removeAdsSkuId": "remove_ads",
            "rewarded": {
                "enabled": False,
                "optInOnly": True,
                "showExactRewardPreview": True,
                "forbidDdaRiggingForRevive": True,
                "maxPerSession": 5,
                "placements": rewarded_by_genre.get(genre, rewarded_by_genre["other"]),
            },
            "interstitial": {
                "enabled": False,
                "boundaryOnly": True,
                "onboardingGraceMatches": 3,
                "minIntervalSeconds": 180,
                "minMatchesBetween": 2,
                "suppressAfterConsecutiveLosses": 2,
            },
            "banner": {
                "enabled": False,
                "hideDuringGameplay": True,
                "safeMarginPx": 16,
                "allowedScreens": ["lobby", "pause", "summary"],
            },
        },
        "purchaseScreens": {
            "enabled": False,
            "providerMode": "mock" if iap_provider != "mock" else "mock",
            "showRealMoneyEquivalent": True,
            "requireTwoStepConfirmation": True,
            "preventBundlePriceMismatch": True,
            "showDropOddsAndPity": True,
            "allowFakeResettingTimers": False,
            "requireRestorePurchasesButton": True,
            "categories": ["Featured", "Cosmetics", "Remove Ads"],
            "catalog": [
                {
                    "sku": "remove_ads",
                    "title": "Remove Interstitial & Banner Ads",
                    "category": "Remove Ads",
                    "type": "non_consumable",
                    "priceUsd": 2.99,
                    "description": "Permanently disables all interstitial and banner ads; keeps optional rewarded bonuses.",
                },
                {
                    "sku": "starter_cosmetic_pack",
                    "title": "Starter Cosmetic Pack",
                    "category": "Cosmetics",
                    "type": "cosmetic_direct",
                    "priceUsd": 1.99,
                    "softCurrencyGrant": 0,
                    "description": "Cosmetic-only skin bundle with zero gameplay or matchmaking stat advantage.",
                },
            ],
        },
        "wellbeingProtocol": {
            "layer1_grayscaleEnabled": False,
            "layer1_grayscaleBrightnessCap": 0.40,
            "layer2_cognitiveFrictionSeconds": 20,
            "layer3_twoLossStopEnabled": False,
            "layer3_twoLossStopMinutes": 30,
            "layer4_economicCoolingOffHours": 48,
            "layer4_disableOneClickBuy": True,
            "layer5_suppressZeigarnikNotifications": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect game engine/genre and generate Beyin-Bedava plan.")
    parser.add_argument("workspace", type=Path, help="Path to target workspace directory.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--emit-config", type=Path, help="Optional path to write recommended beyin-bedava-config.json.")
    args = parser.parse_args()

    root = args.workspace.resolve()
    if not root.is_dir():
        print(f"Error: workspace directory not found: {root}", file=sys.stderr)
        return 1

    files = _collect_files(root)
    is_game, engine, languages, evidence = detect_engine(root, files)
    genre, genre_scores, detected_systems, risk_signals = infer_genre_and_systems(root, files)
    config = build_recommended_config(genre, engine)

    if args.emit_config:
        if not is_game:
            print("Refusing config emission: no confirmed game project.", file=sys.stderr)
            return 2
        if args.emit_config.exists():
            print("Refusing to overwrite existing config; review and migrate manually.", file=sys.stderr)
            return 2
        args.emit_config.parent.mkdir(parents=True, exist_ok=True)
        with args.emit_config.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(config, indent=2) + "\n")

    result: Dict[str, Any] = {
        "workspace": str(root),
        "is_game_project": is_game,
        "engine": engine,
        "languages": languages,
        "evidence": evidence,
        "inferred_genre": genre,
        "genre_scores": genre_scores,
        "detected_systems": detected_systems,
        "static_risk_signals": risk_signals,
        "recommended_config": config,
        "autonomous_action_plan": [
            "Read-only scan; confirm actual game intent and engine.",
            "Select only relevant modules and explicit scope.",
            "Implement only when requested; verify real builds and playtests.",
        ],
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"# Beyin-Bedava Project Scan (`{root.name}`)")
        print(f"- **Game Project:** `{is_game}` | **Engine:** `{engine}` | **Genre:** `{genre}`")
        print(f"- **Languages:** {', '.join(languages) or 'none'}")
        print(f"- **Evidence:** {'; '.join(evidence) or 'None'}")
        print(f"- **Static Risk Signals:** {', '.join(risk_signals.keys()) or 'None detected'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
