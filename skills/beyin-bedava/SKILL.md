---
name: beyin-bedava
description: >-
  Beyin-Bedava / Beyin-bedava autonomous game architecture skill. Activates automatically in any game project without requiring extra commands to inspect the codebase, calibrate matchmaking (SBMM/EOMM), Dynamic Difficulty Adjustment (DDA), virtual economy (Faucets/Sinks, Soft/Hard currency), genre-adapted ad placements (rewarded, interstitial, banner, loss-streak cooldowns), purchase/IAP store screens (real-currency pricing, aligned packs, 2-step confirmation, odds disclosure, Restore Purchases), algorithmic transparency UI, and 5-layer player protection protocols, plus 4-stage telemetry & dark-pattern auditing.
---

# Beyin-Bedava

Autonomous, engine-agnostic game architecture skill grounded in *"Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma"*. When opened in any game workspace, inspect the project automatically, tailor every algorithmic, monetization, ad-placement, purchase-screen, and player-wellbeing layer to the game's genre and aesthetic, implement them cleanly, and verify with simulation and audit tooling.

## Core Thesis Principles & Non-Negotiable Invariants

- **$H_1$ (Algorithmic Manipulation):** EOMM and DDA alter win/loss sequences and physics/combat parameters (hitbox radius, bullet magnetism, damage multipliers, critical-HP damping) below perception thresholds to extend session duration.
- **$H_2$ (Neurobiological Conditioning):** Variable ratio reinforcement, Reward Prediction Error (RPE), artificial near-misses, Zeigarnik tension, and FoMO timers sustain mesolimbic dopamine signaling and weaken prefrontal self-regulation.
- **$H_3$ (Structured Friction & Protection):** Visual suppression, cognitive friction, loop interruption, and economic isolation outperform passive willpower restrictions.
- **Mandatory Transparency & Ethical Monetization Rule:** Whenever matchmaking optimization, DDA, ads, or IAP screens exist in a game, you MUST wire:
  1. Schema-driven `beyin-bedava-config.json` conforming to [beyin-bedava-config.schema.json](resources/beyin-bedava-config.schema.json) (zero hardcoded magic weights).
  2. Player-accessible **Algorithmic Transparency & Drop-Odds** disclosure UI.
  3. Toggleable **5-Layer Player Protection** safeguards (`Layer 1–5`).
  4. Anti-dark-pattern **Ad Placements** and **Purchase/IAP Screens** (`gamma_monetization = 0.0` default, no mid-action interstitials, no loss-streak ad punishment, no remainder-mismatch currency traps, no 1-click accidental buys).

## Operating Modes

Default to full autonomous **`INTEGRATE`** whenever a game project is opened or created, unless the user requests a focused **`AUDIT`**, **`SIMULATE`**, or **`PROTECT`** pass.

1. **`INTEGRATE` (Zero-Command Autonomous Integration):** Auto-detect engine/genre, generate `beyin-bedava-config.json`, implement Telemetry, Matchmaking, DDA, Virtual Economy, **Ad Placements**, **Purchase/IAP Screens**, Transparency UI, and 5-Layer Hygiene modules.
2. **`AUDIT` (4-Stage Diagnostic & Monetization Audit):** Run [detect_game_project.py](scripts/detect_game_project.py) and [audit_telemetry.py](scripts/audit_telemetry.py) against code, configs, ad triggers, store screens, and telemetry logs; classify EOMM, DDA, Ad Dark Patterns, and IAP Dark Patterns; assign Neurobiological Risk (`LOW` / `MEDIUM` / `HIGH`) and remediations.
3. **`SIMULATE` (Stochastic Validation):** Run [simulate_eomm_dda.py](scripts/simulate_eomm_dda.py) calibrated to the game's skill spread, match loop, and DDA bounds; inspect Mann-Whitney U, Welch's t, Cohen's d, and Rank-Biserial $r$.
4. **`PROTECT` (Well-Being & Store/Ad Hardening):** Retroactively add 5-Layer Hygiene, Algorithmic Transparency UI, loss-streak ad suppression, and ethical store guardrails to an existing game.

## Autonomous Zero-Command Workflow (Steps 0–7)

### Step 0: Auto-Inspect the Game Workspace
Run project discovery immediately (do not wait for user prompting):
```bash
python3 ~/.gemini/config/plugins/beyin-bedava/skills/beyin-bedava/scripts/detect_game_project.py "<workspace>" --format json
```
Read [genre-and-engine-adapters.md](references/genre-and-engine-adapters.md). Identify the engine, language, genre, scenes/screens, existing ad SDKs, existing IAP/store code, and static risk signals.

### Step 1: Establish `beyin-bedava-config.json`
Create or update `beyin-bedava-config.json` conforming to [beyin-bedava-config.schema.json](resources/beyin-bedava-config.schema.json) (you can bootstrap it via `detect_game_project.py "<workspace>" --emit-config "<workspace>/beyin-bedava-config.json"` and refine genre SKUs/placements).

### Step 2: Implement Telemetry State Vector ($s_i$) & Event Bus
Track anonymized in-session state without PII leakage:
- Rolling match/attempt W/L sequence, consecutive loss counter, session duration vs baseline, latency.
- Real-time performance deltas ($\Delta S_i(t)$, miss streaks, normalized struggle index $\in [0, 1]$).
- Economy inflows/outflows, ad impressions/skips/completions, and store hover/purchase events.

### Step 3: Implement Matchmaking & Genre-Adapted DDA
Read [math-and-algorithms.md](references/math-and-algorithms.md) and implement decoupled modules:
- **Matchmaking:** SBMM cost $|P(\text{Win}) - 0.50|$, EOMM churn-minimizing assignment, or weighted suitability $S(m)$ (`gamma_monetization = 0.0` in production).
- **DDA Controller:** Bounded hitbox/hurtbox scaling (`<= 1.25x`), bullet/aim magnetism (`<= 0.25`), net damage scaling $\Phi$ (`<= 1.18x`), and critical-HP exponential damping below $H_{\text{crit}}$.

### Step 4: Implement Virtual Economy & Behavioral Pacing
Read [neurobiology-and-economy.md](references/neurobiology-and-economy.md). Implement explicit Faucet/Sink tracking, bounded Variable Ratio drops with deterministic hard pity counters, and Zeigarnik-safe progression (no punitive streak resets or fake scarcity timers).

### Step 5: Architect & Implement Ad Placements and Purchase / IAP Screens
Read [ads-and-iap-architecture.md](references/ads-and-iap-architecture.md) and adapt directly to the game's core loop and UI theme:
- **Ad Placement Engine (`AdPlacementManager` + `IAdProvider`):**
  - *Rewarded Ads:* Opt-in only, explicit reward preview before watching, daily/session faucet cap, strictly **forbid rigging DDA to force ad revives**.
  - *Interstitial Ads:* Trigger only at natural boundaries (post-match, level complete, return-to-menu); honor onboarding grace period (`>= 3` matches), minimum cooldown (`120–180s` & `2–3` matches), and **automatically suppress after `>= 2` consecutive losses** (`L-L` / `L-L-L` churn protection).
  - *Banner Ads:* Lobby/pause/summary screens only, hidden during active gameplay, `>= 16px` safe clearance from interactive CTAs, zero layout shift.
  - *Remove-Ads Entitlement & Consent:* Instantly disables interstitials/banners when purchased; defaults to `MockAdProvider` and official test ad-unit IDs (never live secrets).
- **Purchase / IAP Screen (`StoreManager` + Store UI + `IIAPProvider`):**
  - *Layout & Anatomy:* Currency & Transparency Header (with **Restore Purchases** button), Featured / Remove-Ads banner, Category tabs (`Featured`, `Cosmetics`, `Currency Packs`, `Battle Pass`, `Remove Ads`), Item Detail & **2-Step Confirmation Modal**.
  - *Anti-Dark-Pattern Invariants:* Display real-money equivalents next to virtual prices, align currency pack denominations (prevent remainder traps), publish exact drop odds & pity counters, enforce Layer 4 optional 48h cooling-off/cap, and keep `gamma_monetization = 0.0` (no post-purchase skill relaxation). Default to `MockIAPProvider` / sandbox receipts.

### Step 6: Wire Algorithmic Transparency & 5-Layer Player Protection
Read [protection-and-audit-protocol.md](references/protection-and-audit-protocol.md) and integrate all 5 layers + disclosure screen:
1. **Visual Cortex Suppression:** Grayscale post-process/shader toggle + 40% luminance cap.
2. **Cognitive Friction:** Disable auto-requeue/auto-start; 20+ second deliberate confirmation/countdown.
3. **EOMM Loop Interruption:** "2-Loss Stop" rule — 30-minute break/cooldown after 2 consecutive losses.
4. **Economic Isolation:** No 1-click buy, real-currency pricing, 48-hour purchase cooling-off / cap.
5. **Notification & Zeigarnik Hygiene:** Suppress streak/energy/event notifications and allow hiding incomplete task badges.

### Step 7: Verify End-to-End
Run all checks before declaring completion:
- Execute [simulate_eomm_dda.py](scripts/simulate_eomm_dda.py) calibrated to project settings.
- Execute [audit_telemetry.py](scripts/audit_telemetry.py) against sample/recorded telemetry covering matchmaking, DDA, economy, ads, and purchase screens.
- Build and run the target game project's own test suite / runtime verification.

## References & Tooling

- **Mathematical Models & Pseudocode:** [math-and-algorithms.md](references/math-and-algorithms.md)
- **Neurobiology, RPE, Zeigarnik & Economy:** [neurobiology-and-economy.md](references/neurobiology-and-economy.md)
- **Ad Placements & Purchase/IAP Architecture:** [ads-and-iap-architecture.md](references/ads-and-iap-architecture.md)
- **5-Layer Protection & 4-Stage AI Audit:** [protection-and-audit-protocol.md](references/protection-and-audit-protocol.md)
- **Genre Matrix & Engine Blueprints:** [genre-and-engine-adapters.md](references/genre-and-engine-adapters.md)
- **APA 7 Bibliography & Patents:** [bibliography.md](references/bibliography.md)
- **Config JSON Schema:** [beyin-bedava-config.schema.json](resources/beyin-bedava-config.schema.json)
- **Autonomous Project Detector:** [detect_game_project.py](scripts/detect_game_project.py)
- **Stochastic EOMM/DDA Simulator:** [simulate_eomm_dda.py](scripts/simulate_eomm_dda.py)
- **4-Stage Telemetry Auditor:** [audit_telemetry.py](scripts/audit_telemetry.py)

## Definition of Done (Quality Gates)

1. `beyin-bedava-config.json` exists, validates against schema, and drives all parameters (zero hardcoded magic weights).
2. Matchmaking & DDA modifiers remain bounded, transparent, and genre-adapted.
3. Ad placements respect natural boundaries, onboarding grace, frequency caps, Remove-Ads entitlement, and `>= 2` consecutive-loss suppression.
4. Purchase/IAP screens render with real-money equivalents, aligned bundles, 2-step confirmation, odds/pity disclosure, Restore Purchases, and `MockIAPProvider`/sandbox safety.
5. Algorithmic Transparency UI and all 5 Digital Hygiene layers are wired and toggleable.
6. Simulation, 4-stage audit, and game project tests/builds pass cleanly.
