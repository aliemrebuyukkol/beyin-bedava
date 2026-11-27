# Changelog

## 3.1.0

- Modularized `beyin-bedava-config.schema.json` with `enabledModules` conditional subsystem requirements while preserving backward compatibility for 2.0, 2.1, and 3.0 configs.
- Added numeric threshold/range comparators (`lte`, `lt`, `gte`, `gt`, `between`, `approx`/`tol`) to `integration.schema.json` and `plan_game_integration.py`.
- Cleaned up `detect_game_project.py` (removed dead provider ternary expressions, added `--minimal` config emission, expanded `SKIP_DIRS` and `.xcodeproj`/`.xcassets` suffixes, restricted genre/risk scanning to source/manifest files, and added `detect_all_engines` multi-engine reporting).
- Added `upgrade` (`--upgrade`) and Antigravity `--global-plugin` / `--plugin-dir` synchronization to `install_skill.py`.
- Extended `task_ledger.py` with plan-configurable `owners`, configurable `reopen --attempts`, and `check-files --git-root` worktree verification.
- Extended `audit_gameplay.py` to audit state-graph reachability and timing-window fairness alongside grid levels.
- Added `fair-window-scoring` and `bounded-pity-drop` tasks to `benchmarks/tasks.json` and `token_overhead_ratio` reporting to `benchmarks/run.py`.

## 3.0.0

- Added a scoped knowledge catalog, source-linked research plans, and a versioned runtime verification contract with Godot and custom terminal producers. Extended project detection and corrected engine labels.

## 2.1.0

- Added a persistent Python task ledger with a task graph, lease fencing, checkpoints, bounded retries and coordinated file ownership for Beyin-Bedava and Tasarım Vergisi.
- Added executable Pulse Gate examples for Swift, SpriteKit, RealityKit, Unity, Godot, Three.js and Flutter/Flame.
- Added grid gameplay auditing and measurable criteria for player motivation, design alternatives, input feedback and emotional experience.
- Added telemetry validation, coverage reporting, provenance and sample/applicability controls for screening.
- Replaced player-level simulation significance tests with independent paired synthetic cohorts and a paired bootstrap interval.
- Added host-specific installers, a Codex discovery check and nonce-based native activation checks for Codex, Claude Code and Antigravity.
- Added a paired skill-context benchmark with Codex CLI and OpenAI-compatible inference backends. Test and benchmark outcomes are in the [release evidence](benchmarks/REPORT.md).

## 2.0.0

- Added player-first design modules, scoped execution and quality guidance, project detection, a safe-by-default configuration schema, and a synthetic simulator and telemetry auditor.
