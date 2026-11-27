# Beyin-Bedava 2.1.0 release evidence

## Paired skill benchmark

The runner sends the same three game-design tasks to the same model with and without selected Beyin-Bedava context. Each pair gets its own fresh model requests. A fixed schedule seed randomizes task order, and opposite condition orders alternate within each task. The chat backend also sends the same seed within each pair. The on arm appends the skill entry point, creative mechanics and game feel modules. This measures the effect of presenting skill context for constrained tasks. Native discovery and activation have separate verification.

| Metric | Evaluation |
| --- | --- |
| Creativity indicator | Fraction of three alternatives with distinct axes, distinct rule text, a choice and feedback. Phrase structure and diversity stand in for a human review of novelty and fit. |
| Code quality | Mean of supported syntax, bounded integer behavior over the whole declared input domain and simple control flow (at most four ternaries). |
| Task completion | Fraction of deterministic acceptance cases passed. |
| Rule error rate | Fraction of domain evaluations with errors or values outside the contract. Invalid model documents or unsafe expressions score one. Provider failures are counted separately. |
| Tokens and time | Provider-reported input, cached input and output counts where available, plus client-side wall time. |

[Codex CLI attempt](codex-attempt.json) invoked gpt-5.4 once per condition. Both calls failed authentication before producing model output. Comparative quality, consumption and latency fields are null for that run. The [local Qwen benchmark](qwen-local.json) completed six counterbalanced pairs, two per task. It used Qwen2.5-Coder-1.5B-Instruct Q4_K_M on llama.cpp build 12800 with two CPU threads and the provider's default prompt cache enabled. The model SHA-256, prompts' context and task hashes, inference seeds and raw outputs are in the JSON. The [first six-pair pilot](qwen-pilot.json) used simple random ordering and is retained separately.

| Mean per call | Skill off | Skill on | On minus off |
| --- | ---: | ---: | ---: |
| Creativity indicator | 50.0% | 100.0% | +50.0 percentage points |
| Code quality | 66.7% | 83.3% | +16.7 percentage points |
| Task completion | 46.8% | 61.1% | +14.3 percentage points |
| Rule error rate | 33.3% | 16.7% | −16.7 percentage points |
| Input tokens | 217 | 1,990 | +1,773 |
| Cached input tokens | 216 | 1,989 | +1,773 |
| Output tokens | 244 | 228 | −16 |
| Total tokens | 461 | 2,218 | +1,757 |
| Wall time | 9.72 s | 11.88 s | +2.16 s |
| Provider error rate | 0% | 0% | 0 percentage points |

The main run used a warm local server after the pilot. Token totals include cached input and the latency averages describe this environment's warm-cache behavior. Six paired tasks on a single small model give a descriptive result. Creativity scores reflect the rule-based rubric. The run leaves native Codex performance and human ratings unmeasured.

To reproduce the local comparison, serve the same GGUF through llama.cpp and use:

```bash
python benchmarks/run.py --chat-url http://127.0.0.1:4187/v1/chat/completions \
  --model qwen2.5-coder-1.5b-instruct-q4-k-m --repeats 2 --seed 42 \
  --model-revision sha256:cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046 \
  --output /tmp/beyin-ab.json
```

The [GGUF revision](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/tree/f86cb2c1fa58255f8052cc32aeede1b7482d4361) and [llama.cpp build](https://github.com/ggml-org/llama.cpp/releases/tag/b12800) are public.

## Local verification

| Check | Observed result |
| --- | --- |
| Existing 2.0 tests | 10 passed at baseline commit 2a9e424. |
| Python 3.10.22 and 3.12.14 | 26 tests passed per version. Includes task persistence, recovery, conflict and dependency gates, provenance, validation, benchmark scoring and installers. |
| Gameplay audit | Fixture returned 0 issues. Shortest paths had 2 and 3 moves. |
| Experience evaluator | Example plan returned missing for each of three criteria and exited 2. Human playtest evidence remains pending. |
| Synthetic simulation | 20 pairs, 50 synthetic players per policy per pair, 20 rounds and seed 42. The model-only mean change was +1.790 matches with a paired bootstrap interval of 1.542 to 2.070 using minimum-cost assignment. |
| Godot 4.7.2 | Headless scene buttons verified insufficient charge, win and reset. |
| Three.js 0.180.0, Node 24.22.3 | Unit test and Vite production build passed. Playwright drove Chromium against the built site and observed the WebGL smoke marker. |
| Flutter 3.29.3, Flame 1.27.0 | Widget input test and web build passed. |
| Swift 6.0.3 on Linux | Swift test passed. Interactive console accepted the charge, blocked pulse, win and reset sequence. |
| SpriteKit and RealityKit | macOS rendering and input remain unverified locally. The macOS CI job checks compilation and the shared rule test. |
| Unity 6 | The editor and license were unavailable. The Unity smoke command remains unexecuted. |
| Host installation | File-install and nonce-verifier tests passed for all three paths. Codex app-server independently listed the installed skill as enabled. |
| Native host activation | Codex model authentication failed. Claude Code and Antigravity native sessions are unverified. |
| Tasarım Vergisi | The two-owner protocol was exercised through the ledger tests. Joint native-host execution remains unverified. |

Use the [demo commands](../skills/beyin-bedava/adapters/DEMOS.md) and [README](../README.md) to rerun the checks. The [simulation artifact](simulation.json) is labeled synthetic and contains no observed player data.
