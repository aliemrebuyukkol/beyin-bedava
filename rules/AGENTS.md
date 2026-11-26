# Beyin-Bedava Autonomous Game Architecture Rule

## 1. Activation Gate (Game Projects Only)
Activate this rule **only** when the active workspace or user request is a digital game project — evidenced by markers such as `project.godot`, `ProjectSettings/ProjectVersion.txt`, `*.uproject`, `Assets/*.unity`, game dependencies in `package.json` / `Cargo.toml` / `pyproject.toml` / `requirements.txt` (`phaser`, `pixi.js`, `three`, `babylonjs`, `kaboom`, `excalibur`, `pygame`, `arcade`, `bevy`, `macroquad`, `love` / `conf.lua`), or explicit game creation/editing intent. Remain completely dormant in non-game repositories.

## 2. Zero-Command Autonomous Execution Protocol
Whenever you open or work inside a game project, do **not** wait for a slash command or manual skill trigger:
1. Immediately read `~/.gemini/config/plugins/beyin-bedava/skills/beyin-bedava/SKILL.md` (or `.agents/skills/beyin-bedava/SKILL.md` if installed locally in the repo) and run:
   `python3 ~/.gemini/config/plugins/beyin-bedava/skills/beyin-bedava/scripts/detect_game_project.py "<workspace>" --format json`
2. Inspect the engine, genre, scenes/UI, existing monetization/matchmaking/difficulty code, and static risk signals.
3. Autonomously design, edit, and implement the full **Beyin-Bedava** architecture tailored to the game's genre and visual identity:
   - **`beyin-bedava-config.json`:** Schema-driven config conforming to `beyin-bedava-config.schema.json` (zero hardcoded magic weights).
   - **Telemetry State Vector ($s_i$) & Event Bus:** Tracks W/L sequence, session duration vs baseline, latency, struggle index, economy flow, ad events, and store events without PII leakage.
   - **Matchmaking & Genre-Adapted DDA:** SBMM/EOMM/Hybrid + bounded DDA (hitbox/hurtbox, aim assist/magnetism, damage scaling, critical-HP damping) calibrated to the game's mechanics. Keep `gamma_monetization = 0.0` unless explicitly simulating research.
   - **Virtual Economy & Behavioral Pacing:** Balanced Faucets/Sinks, bounded Variable Ratio with hard pity counters, non-punitive progression.
   - **Ad Placements (`AdPlacementManager`):** Genre-fitted Rewarded (opt-in only, exact reward preview, never rig DDA to force revives), Interstitial (natural boundary only, >=3 match onboarding grace, 120–180s & 2–3 match cooldown, **auto-suppressed after >=2 consecutive losses**), and Banner (lobby/pause/summary only, hidden during active gameplay, >=16px CTA spacing), plus `MockAdProvider` / test IDs.
   - **Purchase / IAP Screens (`StoreManager` + Store UI):** Genre-fitted store layout with real-money price equivalents, aligned currency packs (no remainder traps), 2-step confirmation (no 1-click checkout), disclosed drop odds & pity counters, Restore Purchases button, optional 48h cooling-off/cap guard, and `MockIAPProvider` / sandbox adapter.
   - **Mandatory Transparency & 5-Layer Player Protection:** Player-accessible Algorithmic Transparency screen + toggles for Layer 1 (Grayscale + 40% brightness cap), Layer 2 (20s+ cognitive friction), Layer 3 (2-Loss Stop 30m break), Layer 4 (Economic Isolation / 48h cooling-off), and Layer 5 (Notification & Zeigarnik hygiene).
4. Verify with `simulate_eomm_dda.py`, `audit_telemetry.py`, and the project's own build/tests.

## 3. Scope & Safety Boundaries
- **No Live Credentials or Real Charges:** Never embed live production ad-unit secrets, payment keys, or charge real money; default to official test IDs and mock/sandbox providers.
- **Preserve Existing Work & Narrow Edits:** Keep existing user code and visual style intact. When the user requests only a narrow bug fix in a game, preserve `beyin-bedava` invariants without rewriting unrelated systems.
