# Beyin-Bedava 2.1.0 release evidence

## Paired skill benchmark

The runner sends the same three game-design tasks to the same model with and without selected Beyin-Bedava context. Each pair gets its own fresh model requests. A fixed schedule seed randomizes task and condition order. The chat backend also sends the same seed within each pair. The on arm appends the skill entry point, creative mechanics and game feel modules. This measures the effect of presenting skill context for constrained tasks. Native discovery and activation have separate verification.

| Metric | Evaluation |
| --- | --- |
| Creativity indicator | Fraction of three alternatives with distinct axes, distinct rule text, a choice and feedback. Phrase structure and diversity stand in for a human review of novelty and fit. |
| Code quality | Mean of supported syntax, bounded integer behavior over the whole declared input domain and simple control flow (at most four ternaries). |
| Task completion | Fraction of deterministic acceptance cases passed. |
| Rule error rate | Fraction of domain evaluations with errors or values outside the contract. Invalid model documents or unsafe expressions score one. Provider failures are counted separately. |
| Tokens and time | Provider-reported input, cached input and output counts where available, plus client-side wall time. |

[Codex CLI attempt](codex-attempt.json) invoked gpt-5.4 once per condition. Both calls failed authentication before producing model output. Comparative quality, consumption and latency fields are null for that run. Local inference results are being collected from an OpenAI-compatible endpoint.

## Local verification

| Check | Observed result |
| --- | --- |
| Existing 2.0 tests | 10 passed at baseline commit 2a9e424. |
| Python 3.10.22 and 3.12.14 | 24 tests passed per version. Includes task persistence, recovery, conflict and dependency gates, provenance, validation, benchmark scoring and installers. |
| Gameplay audit | Fixture returned 0 issues. Shortest paths had 2 and 3 moves. |
| Experience evaluator | Example plan returned missing for each of three criteria and exited 2. No human playtest was supplied. |
| Synthetic simulation | 20 pairs, 50 synthetic players per policy per pair, 20 rounds and seed 42. The model-only mean change was +0.418 matches with a paired bootstrap interval of 0.116 to 0.736. |
| Godot 4.7.2 | Headless scene buttons verified insufficient charge, win and reset. |
| Three.js 0.180.0, Node 24.22.3 | Unit test and Vite production build passed. Playwright drove Chromium against the built site and observed the WebGL smoke marker. |
| Flutter 3.29.3, Flame 1.27.0 | Widget input test and web build passed. |
| Swift 6.0.3 on Linux | Swift test passed. Interactive console accepted the charge, blocked pulse, win and reset sequence. |
| SpriteKit and RealityKit | macOS rendering and input remain unverified locally. The macOS CI job compiles the Apple implementation. |
| Unity 6 | The editor and license were unavailable. The Unity smoke command remains unexecuted. |
| Host installation | File-install and nonce-verifier tests passed for all three paths. Codex app-server independently listed the installed skill as enabled. |
| Native host activation | Codex model authentication failed. Claude Code and Antigravity native sessions are unverified. |
| Tasarım Vergisi | The two-owner protocol was exercised through the ledger tests. No joint native-host session was available. |

Use the [demo commands](../skills/beyin-bedava/adapters/DEMOS.md) and [README](../README.md) to rerun the checks. The [simulation artifact](simulation.json) is labeled synthetic and contains no observed player data.
