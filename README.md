# Beyin-Bedava 2.0

Game Design Intelligence skill: player-first mechanics, motivation, game feel, progression, platform adapters, scoped execution and ethical optional monetization. The legacy algorithm/economy references remain as research and audit material.

## Install
Clone this repo and copy `skills/beyin-bedava` into the skill directory documented by your host (for example a project-local `.agents/skills/` where supported). Read `rules/AGENTS.md` and merge relevant rules into the host's recognized instruction location if needed. A manifest or Markdown file alone does not install or auto-activate a plugin. Check host discovery before relying on it.

## Modes
SCAN is read-only by default. DESIGN, BUILD/IMPROVE, AUDIT, SIMULATE and MONETIZE/PROTECT route to only applicable modules. No automatic monetization, live churn-based matchmaking or hidden difficulty manipulation. See [SKILL.md](skills/beyin-bedava/SKILL.md).

## CLI
```bash
python3 skills/beyin-bedava/scripts/detect_game_project.py /path/to/game --format json
python3 skills/beyin-bedava/scripts/detect_game_project.py /path/to/game --emit-config /path/to/game/beyin-bedava-config.json
python3 skills/beyin-bedava/scripts/simulate_eomm_dda.py --players 1000 --matches 60 --seed 42 --json
python3 skills/beyin-bedava/scripts/audit_telemetry.py --input telemetry.json --format json
python3 -m pip install -r requirements-test.txt
python3 -m unittest discover -s tests -v
```
Detector is heuristic; config emission refuses non-game/unknown projects or overwrite. Generated config uses disabled-by-default monetization, matching and DDA. Audit flags are hypotheses; insufficient evidence and policy violations exit nonzero. Demo/simulation data are synthetic, not user evidence. No native game runtime is bundled.

## Migration
Existing 1.x configs should be reviewed, not silently overwritten. v2 removes live EOMM/hybrid modes from the config schema, requires zero monetization weight, and tightens DDA ceilings. Opt-in eligible features only; existing 1.x enabled settings are not automatically changed. See [examples](skills/beyin-bedava/examples/game-profiles.md) and [quality gates](skills/beyin-bedava/orchestration/quality.md).

MIT license.

## Örnek proje · Yankı Rotası

Beyin-Bedava 2.1.0 ile geliştirilen dört bölümlük bir Godot bulmacası. Plakalara yankı bırakarak kapıları aç ve istasyondan çık.

[**Tarayıcıda oyna**](https://yanki-rotasi.kafamdakisey.chatgpt.site) (ChatGPT hesabıyla) · [Web sürümünü indir](https://github.com/aliemrebuyukkol/beyin-bedava/archive/refs/heads/gh-pages.zip) · [Godot kaynak projesi ve çalıştırma talimatları](examples/yanki-rotasi/)

Web paketini açtıktan sonra `OYNAT.txt` içindeki adımlarla tarayıcıda çalıştır.
