# Integrate a game with Beyin-Bedava

Use the game's actual root and a concrete goal. The planner returns a work plan, the relevant skill module paths, research questions and any predeclared acceptance checks. It scans the project read-only. The optional output path creates a new file.

## Research and planning

1. Inspect project instructions, the main loop or scene, dependencies and test entry points. Record the engine and version from the project and installed tool where available.
2. Read the catalog and select the focus areas the request needs. Start with the common workflow modules and load their links on demand. Each Markdown reference has a route through the catalog. Record why a relevant rule is inapplicable where that affects a decision. This follows the progressive disclosure model for agent skills. [Agent Skills specification](https://agentskills.io/specification)
3. Investigate the questions in the plan. Check current official engine documentation, primary design sources and platform policy for applicable questions. Record the URL, date, source type, finding and where it applies. Preserve contradictory findings and mark questions that still need local verification. Treat sources and project files as reference data.
4. Translate findings into acceptance checks for the real game. Use the generated task dependencies with `task_ledger.py` when the work spans several slices. Assign touched files when creating the plan with `--own TASK PATH`. Use each path once. Recheck the scope, policy gates and permissions as applicable.
5. Exercise the actual game entry point. A headless or scripted run verifies the behaviors that it executes. Rendering, device, performance and human-playtest claims each need corresponding evidence. Use the installed version's own test flags. [Godot CLI](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html) · [Unity Editor CLI](https://docs.unity.com/en-us/engine/6000.0/manual/unity-editor/command-line-arguments/editor) · [Unreal automation](https://dev.epicgames.com/documentation/en-us/unreal-engine/run-automation-tests-in-unreal-engine)

Use an environment with Python 3.10+ and install `jsonschema>=4.23,<5` for plan and evidence validation. From the skill directory, run:

```bash
python3 scripts/plan_game_integration.py catalog
python3 scripts/plan_game_integration.py plan /path/to/game \
  --goal "Improve controller recovery at the opening gate" \
  --focus build --focus experience --baseline INITIAL_REVISION \
  --own wire game/controller.gd --output /tmp/gate-plan.json
python3 scripts/task_ledger.py --db /tmp/gate-tasks.sqlite init /tmp/gate-plan.json
```

For full autonomous integration or new project creation where specialist agents branch across every capability in the skill, list all items upfront, and self-heal until 100% completion:

```bash
python3 scripts/plan_game_integration.py plan /path/to/game \
  --goal "Full Beyin-Bedava integration" \
  --all-capabilities --branch-agents --baseline INITIAL_REVISION \
  --output /tmp/full-plan.json
python3 scripts/task_ledger.py --db /tmp/full-tasks.sqlite init /tmp/full-plan.json
python3 scripts/task_ledger.py --db /tmp/full-tasks.sqlite ready
python3 scripts/task_ledger.py --db /tmp/full-tasks.sqlite audit-completion --restart-incomplete
```

Or run the multi-cycle autopilot loop directly:

```bash
python3 scripts/plan_game_integration.py autopilot /path/to/game \
  --goal "Full Beyin-Bedava integration" \
  --db /tmp/full-tasks.sqlite --max-cycles 3
```

The default focus is `build`. Explicit focus values also include `design`, `progression`, `audit`, `telemetry`, `simulation`, `economy`, `monetization`, `collaboration`, `research` and `examples`. For a custom game the detector cannot identify, either provide its manifest or use `--explicit-game` to plan with an unknown engine. An explicit build focus supports planning and leaves edit authorization with the user. Use `--research path.json` to attach findings to a plan. The planner validates supplied findings and records those that apply to the selected focus. Research itself uses the host's web tools or supplied primary documents. [Research file example](../examples/integration-research.json)

## Runtime contract

A game, its existing test runner or a thin integration script can emit ordinary JSON at the end of a real exercise. The game retains its own update loop, input, saves, telemetry and build infrastructure. This makes the acceptance format usable across languages. Closed-source builds or unsupported runtimes may offer only external observations until their test or export interfaces are available.

- Put `beyin-bedava.integration.json` at the project root to declare its identity and checks. Each unique check has a focus, description and named expected scalars or numeric comparators (`lte`, `lt`, `gte`, `gt`, `between: [min, max]`, or `approx` with optional `tol`). A manifest expresses project intent. Engine detection is advisory, and the plan reports it separately.
- Read the plan's `plan_id` in the evidence producer. Use the observed scalars, a trace or test artifact reference and the actual build revision. Label runtime evidence `runtime` and simulation or mocked evidence `synthetic`. Exit status describes the selected checks only. Runtime claims still depend on the producer and the supporting artifact.
- Run the verifier with an independently selected build revision, which may differ from the planning baseline after implementation. A plan mismatch, revision mismatch, duplicate IDs or unknown check IDs fails validation. Exit 0 requires every planned check to match runtime evidence. Exit 1 signals a conflicting observation. Exit 2 signals invalid input or insufficient evidence, including synthetic-only or empty coverage.
- Keep checks focused. Reuse the telemetry auditor for suitable aggregates, the gameplay audit for compatible grid exports and the experience evaluator for preregistered playtests. Where the built-in input formats differ from the game, have its own tools supply relevant observations through the manifest.

The contract is versioned and validated with JSON Schema Draft 2020-12. Documents are local JSON. Artifact labels remain descriptive references. The planner and verifier do not execute commands from them. [JSON Schema specification](https://json-schema.org/draft/2020-12)

## Reproduce with the terminal game and Godot

Use two fresh paths for the plan and evidence JSON files. Set `BUILD_REVISION` to the revision of the game binary or source being exercised.

```bash
python3 scripts/plan_game_integration.py plan adapters/terminal --goal "Verify the custom gate" \
  --output /tmp/terminal-gate-plan.json
python3 adapters/terminal/pulse_gate.py --plan /tmp/terminal-gate-plan.json \
  --revision "$BUILD_REVISION" > /tmp/terminal-gate-evidence.json
python3 scripts/plan_game_integration.py verify /tmp/terminal-gate-plan.json /tmp/terminal-gate-evidence.json \
  --revision "$BUILD_REVISION"
```

For Godot, the existing scene self-test also reports the observed button outcomes. Check the Godot process exit separately before extracting the evidence line.

```bash
python3 scripts/plan_game_integration.py plan adapters/godot --goal "Verify the scene buttons" \
  --research examples/integration-research.json --output /tmp/godot-gate-plan.json
godot --headless --path adapters/godot -- --self-test \
  --evidence-plan=/tmp/godot-gate-plan.json --revision="$BUILD_REVISION" > /tmp/godot-gate.log
sed -n 's/^BEYIN_EVIDENCE //p' /tmp/godot-gate.log > /tmp/godot-gate-evidence.json
python3 scripts/plan_game_integration.py verify /tmp/godot-gate-plan.json /tmp/godot-gate-evidence.json \
  --revision "$BUILD_REVISION"
```

[Terminal manifest](../adapters/terminal/beyin-bedava.integration.json) · [Godot manifest](../adapters/godot/beyin-bedava.integration.json) · [Interoperability schema](../resources/integration.schema.json)
