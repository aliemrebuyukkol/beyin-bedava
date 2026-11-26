# Player Protection, Transparency & 4-Stage AI Audit Protocol

Operational specifications from Sections 4.2, 5.1, 6, and 6.1 of *Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma*, extended with Ad Placement and Purchase/IAP Dark Pattern diagnostics.

---

## 1. 5-Layer Evidence-Based Protection & Digital Hygiene Protocol (Section 5.1)

Designed to interrupt the habit loop (**Cue $\to$ Craving $\to$ Response $\to$ Reward**) through concrete environmental and software interventions rather than passive willpower:

| Layer | Concrete Implementation in Game / Device | Targeted Mechanism | Neurobiological / Behavioral Effect |
| :--- | :--- | :--- | :--- |
| **1. Visual Cortex Suppression** | Enable **Grayscale mode** via post-process/shader and cap luminance/brightness at **40%** (`layer1_grayscaleBrightnessCap: 0.40`). | Reward animations, store flash & rarity color coding | Dampens visually triggered phasic dopamine spikes and RPE anticipation. |
| **2. Cognitive Friction** | Disable auto-requeue & auto-login; enforce **20+ second deliberate confirmation/countdown** (`layer2_cognitiveFrictionSeconds: 20`), 2FA for store/account, and optional time-window access scheduler. | Habit automation & impulsive session initiation | Extends access latency beyond 20s, re-engaging prefrontal cortex executive control. |
| **3. EOMM Loop Interruption** | **"2-Loss Stop" Rule:** Automatically end ranked/loop queue or enforce at least a **30-minute cooldown** (`layer3_twoLossStopMinutes: 30`) after 2 consecutive losses. Also suppresses interstitial ads on 2+ losses. | EOMM post-loss baiting & DDA compensation loops | Breaks the algorithm's "reward-with-easy-win" retention window and prevents tilt. |
| **4. Economic Isolation** | Remove saved payment tokens, disable 1-click purchases, show real-currency equivalent, and enforce a **48-hour waiting period** (`layer4_economicCoolingOffHours: 48`) or prepaid cap. | Dual-currency abstraction & FoMO spending pressure | Reactivates mental accounting's *Pain of Paying* brake. |
| **5. Notification & Zeigarnik Hygiene** | Suppress event, energy-refill, and daily-streak push/in-app notifications; allow hiding incomplete quest/pass badges (`layer5_suppressZeigarnikNotifications: true`). | Zeigarnik tension & external cue triggers | Eliminates artificial cognitive tension from unfinished tasks. |

---

## 2. Mandatory Algorithmic Transparency Specification (Section 6)

Whenever a game uses matchmaking, dynamic difficulty, ads, or randomized rewards, include a player-accessible **"Algorithmic Transparency & Fair Play"** panel (Settings $\to$ Fair Play / Well-Being + quick link from Store Header) displaying:
1. **Active Matchmaking Mode:** `SBMM` (pure skill fairness), `EOMM` (engagement-weighted), or `Hybrid`, confirming `gamma_monetization = 0.0` (no pay-to-win matchmaking).
2. **Active DDA Status:** Explicit toggle/indicator showing whether dynamic hitbox, aim magnetism, damage scaling, or critical-HP mercy is active and its exact bounds (e.g., Hitbox max `1.25x`, Damage max `1.18x`).
3. **Reward Odds & Pity Counters:** Exact drop probabilities for any randomized reward loop and real-currency cost alongside virtual currency prices.
4. **Ad Frequency & Cooling-Off Status:** Active interstitial cooldown timer, loss-streak ad suppression status, and 5-Layer Hygiene quick toggles.

---

## 3. 4-Stage Autonomous AI Agent Diagnostic & Intervention Pipeline (Section 6.1)

Executed by `scripts/audit_telemetry.py` or during an `AUDIT` review:

### Stage 1: Telemetry & Pattern Diagnosis
Analyze recent session logs, ad cadence, store events, and configuration:
- Rolling Win/Loss sequence (`W/L` variance, max consecutive losses, post-loss win rebound rate).
- Average session duration vs historical player baseline (`session_duration / baseline_duration`).
- Store interaction frequency, hover-to-match correlations, and impulsive purchase rate.
- Ad frequency: mid-gameplay interstitials, interstitials triggered on 2+ loss streaks, banner/CTA overlap.
- Real-time accuracy/damage deltas ($\Delta S_i(t)$) and low-HP survival clustering.

### Stage 2: Algorithmic Classification
Flag active manipulation layers using empirical signatures:
- **`EOMM` Flag:** Consecutive 2–3 loss streaks followed by sharp win-rate rebound (>=70% win rate immediately after 2+ losses) or abnormally low `L-L-L` vs high `W-L-W` match scheduling.
- **`DDA` Flag:** Inconsistent hit registration / accuracy jump (>=12% spike during struggle), damage multiplier deviations (>1.05x), or clustered survival below $H_{\text{crit}}$ (`<= 15%` HP) or rigged deaths pushing rewarded-ad revives.
- **`DARK_PATTERN` (Economy / IAP / Ads) Flag:** Dual-currency separation without real-money display, pack-vs-price remainder mismatch, active FoMO or resetting countdown timers, 1-click purchase flow, undisclosed loot odds, missing Restore Purchases button, post-purchase skill relaxation ($\gamma > 0$), mid-gameplay interstitials, interstitials shown after 2+ consecutive losses, or banner overlap with primary CTAs.

### Stage 3: Neurobiological Risk Scoring (`0–100`)
Weighted composite index across 4 behavioral exposure dimensions (25 pts each):
1. **Variable Ratio Exposure (0–25):** Loot/gacha pull rate, EOMM `W-L-W` oscillation density.
2. **RPE & Near-Miss Density (0–25):** Clutch survival rate below $H_{\text{crit}}$ + rigged near-miss frequency + DDA-forced ad revives.
3. **Zeigarnik & FoMO Pressure (0–25):** Active streak penalties, energy timers, expiring passes, fake timers, notification frequency, forced ad pressure.
4. **Session Escalation & Spend Impulsivity (0–25):** Session duration overrun (`>1.25x` baseline), rapid/1-click microtransactions, and loss-streak interstitial tilt triggers.

Risk Tier Mapping:
- **`LOW` (0–33):** Healthy engagement; maintain baseline transparency and optional hygiene toggles.
- **`MEDIUM` (34–66):** Moderate conditioning signals; recommend enabling Layer 1 (Grayscale/Dim), Layer 2 (20s Friction), Layer 5 (Notification Hygiene), and ad/store guardrails.
- **`HIGH` (67–100):** High dopamine-desensitization & compulsive-loop risk; enforce all 5 layers including Layer 3 (2-Loss Stop, 30m break), Layer 4 (Economic Isolation, 48h cooling-off), loss-streak ad suppression, and 2-step IAP confirmation.

### Stage 4: Friction Protocol Assignment & 4-Week Evaluation (Section 4.2)
Assign targeted environmental interventions (plus concrete Ad/Store code fixes) and track efficacy over a 4-week pre/post window using three KPIs:
1. **Weekly Playtime** (system telemetry hours/week).
2. **Impulsive Microtransaction Count** (unplanned/1-click spend events/week).
3. **Brief Self-Control Scale** score (Wood & Rünger, 2016; Alter, 2017).
