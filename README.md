# Beyin-Bedava 3.1.0

Game design intelligence for player-first mechanics, motivation, game feel and progression. The skill chooses relevant modules for each task. Python tools make planning, recovery and quality checks reproducible.

## Install and verify

Clone this repository. From its root, run the installer with the target game's existing project path.

| Host | Install command | Native verification |
| --- | --- | --- |
| Codex | `python skills/beyin-bedava/scripts/install_skill.py codex install --project /path/to/game` | Run the same command with `discover` to query Codex's skill inventory. Invoke `$beyin-bedava` for the activation probe. |
| Claude Code | `python skills/beyin-bedava/scripts/install_skill.py claude-code install --project /path/to/game` | Invoke `/beyin-bedava` in a fresh Claude Code session from the target project. |
| Antigravity | `python skills/beyin-bedava/scripts/install_skill.py antigravity install --project /path/to/game` | Invoke `/beyin-bedava` in a fresh Antigravity workspace session. Use `--global-plugin` with `install`, `upgrade`, or `check` to sync the global Antigravity plugin directory. |

Use `upgrade` (or `--upgrade`) to replace an existing installation cleanly, and `check` to compare the installed files with this checkout. For an activation check, use a disposable project and run `prepare` in place of `install` after installing. Copy the printed positive and negative prompts into separate fresh sessions on that host. Save each final response as plain text and run `verify --project /path/to/game --response positive.txt --control negative.txt` with the same script and host. The verifier checks an unpredictable value read from the installed skill, plus a non-game control. Keep probe files out of version control and discard the temporary project after testing. An installation, a discovery result and a native response are separate checks. See the [Codex](https://developers.openai.com/codex/skills), [Claude Code](https://code.claude.com/docs/en/skills) and [Antigravity](https://antigravity.google/docs/skills) skill documentation.

## Integrate with a game

Use the [research and integration workflow](skills/beyin-bedava/orchestration/integration.md) to select from the full knowledge catalog, record source findings, plan the work, and validate engine-neutral runtime evidence. Projects based on custom or proprietary engines can declare their own checks through a versioned JSON contract (`expect` supports exact scalars and numeric comparators `lte`, `lt`, `gte`, `gt`, `between`, `approx`/`tol`). The game or its test runner supplies observations from its existing runtime. The repository includes a terminal game and a Godot scene as working producers.

## Workflows

SCAN opens with a read-only project inspection (`--minimal` emits a modular config with `enabledModules: []`). DESIGN, BUILD/IMPROVE, AUDIT, SIMULATE and MONETIZE/PROTECT load only the modules applicable to the goal. Monetization and adaptive difficulty are disabled by default. DDA is visible and opt-in where suitable. Churn and spending remain outside live competitive matchmaking. See the [skill](skills/beyin-bedava/SKILL.md).

Run these commands from the repository root using Python 3.10 or newer.

```bash
python skills/beyin-bedava/scripts/detect_game_project.py /path/to/game --format json
python skills/beyin-bedava/scripts/task_ledger.py init benchmarks/examples/tasks.json
python skills/beyin-bedava/scripts/task_ledger.py check-files TASK_ID TOKEN --git-root /path/to/game
python skills/beyin-bedava/scripts/task_ledger.py status
python skills/beyin-bedava/scripts/audit_gameplay.py benchmarks/examples/gameplay.json
python skills/beyin-bedava/scripts/evaluate_experience.py benchmarks/examples/experience-plan.json
python skills/beyin-bedava/scripts/simulate_eomm_dda.py --players 100 --matches 20 --replicates 20 --seed 42 --json
python skills/beyin-bedava/scripts/audit_telemetry.py --input telemetry.json --format json
```

- The ledger persists a task graph, checkpoints, retry budgets (`reopen --attempts N`), custom plan `owners`, leases, and single-writer file ownership (including `--git-root` worktree verification). It records acceptance evidence supplied by the operator. Replace the example's baseline and files before using it on a real project. See the [execution protocol](skills/beyin-bedava/orchestration/execution.md) and [Tasarım Vergisi collaboration](skills/beyin-bedava/orchestration/skill-router.md).
- The gameplay audit checks grid, state-graph, and timing-window exports for reachability, key and move constraints, difficulty jumps, unused mechanics, mechanic combinations, repeated layouts, and reaction-window fairness. The experience evaluator checks preregistered thresholds against declared evidence. The empty example plan intentionally produces missing statuses. See the [experience criteria](skills/beyin-bedava/intelligence/emotional-experience.md).
- Telemetry declares `provenance.kind` as `observed` or `synthetic` and supplies a `provenance.source` reference. Use opaque IDs and aggregate data. Unknown or absent fields remain unknown. The JSON output records missing fields, applicability and screening status. Exit 0 means complete observed coverage with no screening signal, 1 requests review, and 2 means invalid, insufficient or synthetic-only evidence without a flag. See the [telemetry contract](skills/beyin-bedava/orchestration/telemetry.md).
- Simulation reports a paired-cohort interval over independent synthetic replications. It records the seed, model assumptions and simulation horizon. The independent DDA curve tests parameter bounds. Neither output measures real player behavior.

## Engine examples and verification

The [Pulse Gate examples](skills/beyin-bedava/adapters/DEMOS.md) cover Swift, SpriteKit, RealityKit, Unity, Godot, Three.js and Flutter/Flame. The [release evidence](benchmarks/REPORT.md) records which checks ran and which need additional tooling.

```bash
python -m pip install -r requirements-test.txt
python -m compileall -q skills/beyin-bedava/scripts benchmarks
python -m unittest discover -s tests -v
python benchmarks/run.py --model YOUR_CODEX_MODEL --repeats 4 --output /tmp/beyin-ab.json
```

For OpenAI-compatible inference, supply `--chat-url https://your-provider/v1/chat/completions` and, when required, `--api-key-env NAME`. The benchmark counterbalances condition order within each task. It records deterministic task tests, rule quality, creativity indicators, errors, provider-reported tokens (including `token_overhead_ratio`) and latency. See the [benchmark method and results](benchmarks/REPORT.md).

## Migration

Existing 2.0, 2.1, and 3.0 configurations remain readable. Newly emitted configurations identify 3.1.0, and modular configurations can declare only `schemaVersion`, `gameGenre`, and `enabledModules`. Review 1.x configs before opting into eligible features. The detector leaves existing files in place. Audit inputs from 2.0 can produce incomplete coverage until provenance, store applicability, interval sample counts and DDA comparison context are supplied. The simulation retains descriptive output fields and omits player-level p-values because players share lobbies. See the [changelog](CHANGELOG.md).

MIT license.

## Örnek proje · Yankı Rotası

Beyin-Bedava 2.1.0 ile geliştirilen telefon ve masaüstü düzenleri olan altı bölümlük bir Godot bulmacası. Plakalara yankı bırakarak kapıları aç ve istasyondan çık.

[**Tarayıcıda oyna**](https://yanki-rotasi.kafamdakisey.chatgpt.site) (ChatGPT hesabıyla) · [Web sürümünü indir](https://github.com/aliemrebuyukkol/beyin-bedava/archive/refs/heads/gh-pages.zip) · [Godot kaynak projesi ve çalıştırma talimatları](examples/yanki-rotasi/)

Web paketini açtıktan sonra `OYNAT.txt` içindeki adımlarla tarayıcıda çalıştır.
