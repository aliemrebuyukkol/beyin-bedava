# Neurobiology, Behavioral Loops & Virtual Economy

> **v2 scope:** Legacy research/reference material, not default implementation. Live matchmaking must be fair and independent of churn or spending; hidden outcome manipulation is prohibited. Numerical thresholds and neurobiological claims are hypotheses, not universal or clinical evidence. Optional protections must respect accessibility and genre. Use the v2 SKILL.md and schema in any conflict.

Design and audit specifications from Sections 2.4, 3.1, and 3.2 of *Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma*.

---

## 1. Neurobiological Conditioning Mechanisms

### 1.1 Variable Ratio Reinforcement (Skinner, 1953)
- **Mechanism:** Rewards delivered after an unpredictable number of actions produce the highest resistance to behavioral extinction compared to fixed-ratio or fixed-interval schedules.
- **Game Manifestations:** Loot boxes, gacha banners, procedural rare drops, and EOMM's undulating win/loss cadence (`W-L-W`).
- **Healthy / Transparent Design:**
  - Always publish exact drop rates and pity-counter progress.
  - Provide deterministic milestone paths alongside random drops so players are never trapped in unbounded variance.
- **Dark Pattern Red Flag:** Hidden dynamic drop-rate manipulation (e.g., boosting odds only after churn risk rises or spend stops) or undisclosed pity resets.

### 1.2 Reward Prediction Error — RPE (Schultz, 2016) & Near-Miss (Clark et al., 2009)
- **Mechanism:** Phasic dopamine release along the mesolimbic pathway (Ventral Tegmental Area $\to$ Nucleus Accumbens) encodes **Reward Prediction Error** ($\text{RPE} = \text{Received} - \text{Expected}$) rather than reward magnitude alone. Uncertain reward expectations sustain peak dopaminergic arousal.
- **Near-Miss Effect:** Neuroimaging demonstrates that narrowly missing a reward activates nearly identical reward circuitry to winning, motivating repeated attempts.
- **Game Manifestations:** Slot-like loot reveals slowing down adjacent to mythic items, "1% boss HP remaining" / $H_{\text{crit}}$ clutch escapes, or ranked promotion matches missed by 1 point.
- **Healthy / Transparent Design:**
  - Avoid theatrical near-miss animations on paid/RNG draws.
  - Keep progression feedback proportional and informative rather than artificially tantalizing.
- **Dark Pattern Red Flag:** Visual/audio rigging that displays false near-misses on predetermined RNG rolls or artificially induces 1% HP survival spikes specifically to prevent session quit.

### 1.3 Zeigarnik Effect (Zeigarnik, 1927) & FoMO (Holte & Ferraro, 2020)
- **Mechanism:** Incomplete tasks persist in working memory longer than completed ones, generating cognitive tension. Time-limited events amplify **Fear of Missing Out (FoMO)**, suppressing rational prefrontal cortex decision-making.
- **Game Manifestations:** Battle Passes with expiring tiers, daily login streaks with harsh reset penalties, recharging energy bars, and countdown shop offers.
- **Healthy / Transparent Design:**
  - Non-expiring or archive-accessible seasonal passes.
  - Streak freezes / weekly quotas instead of punitive daily check-ins.
  - Player-controllable notification opt-outs and ability to collapse/hide incomplete quest trackers.
- **Dark Pattern Red Flag:** Aggressive push notifications for regenerating energy, fake scarcity countdown timers that reset, or punitive loss of earned progress upon missing a day.

### 1.4 Chronic Hyper-Stimulation & Neuroplasticity (Volkow et al., 2011)
- **Mechanism:** Chronic high-frequency dopamine stimulation triggers **downregulation of striatal D2 dopamine receptors**, desensitizing individuals to natural everyday rewards and narrowing reward sensitivity toward high-intensity game stimuli.
- **Design Implication:** Games should include natural pacing valleys, calm visual modes (Grayscale/low-luminance option), and session break cues rather than continuous high-arousal sensory bombardment.

---

## 2. Virtual Economy & Dark Patterns (Section 2.4)

### 2.1 Faucets and Sinks Balance (Zagal et al., 2013)
- **Faucets (Musluklar):** Match rewards, quest payouts, login grants, and monetization packs injecting currency into the economy.
- **Sinks (Giderler):** Upgrades, crafting fees, cosmetic unlocks, entry tickets, and repair costs removing currency to prevent hyperinflation.
- **Audit Rule:** Track net inflation rate ($\frac{\text{Faucets} - \text{Sinks}}{\text{Active Supply}}$). Intentional faucet starvation right before paywalls signals engineered progression friction ("pay-to-skip").

### 2.2 Dual Currency & Pain of Paying (Prelec & Loewenstein, 1998)
- **Mechanism:** Separating earned **Soft Currency** (gold/coins) from real-money **Hard Currency** (gems/crystals) abstracts mental accounting and dulls the psychological *Pain of Paying*.
- **Bundle-to-Price Mismatch & Sunk Cost Fallacy:** Pricing store items at e.g. `1,200 gems` while selling packs of `1,000` or `2,500 gems` leaves persistent leftover balances, nudging players into repeat top-ups and Sunk Cost commitment.

### Ethical Economy Checklist

| Economic Pattern | Predatory / Dark Pattern | Ethical & Transparent Alternative |
| :--- | :--- | :--- |
| Currency Display | Hard currency only, obscuring real cost | Show real-money equivalent alongside virtual currency |
| Pack Sizing | Intentional remainder mismatch (e.g., 1000 pack vs 1200 item) | Exact-price checkout or aligned denominations (`preventBundlePriceMismatch: true`) |
| Checkout Friction | Saved cards + 1-click purchase | Explicit confirmation step + optional 48h cooling-off/cap |
| Scarcity Timers | Artificial countdowns on rotating essentials | Stable catalog or clear permanent return dates |

---

## 3. Mechanism-to-Implementation Mapping

| Mechanism | System Implementation Role | Audit Detection Signal | Mitigation / Protection Layer |
| :--- | :--- | :--- | :--- |
| **Variable Ratio** | Loot tables, gacha, EOMM cadence | Unbounded streak variance, hidden odds | Publish odds, hard pity ceiling |
| **RPE & Near-Miss** | Reveal UX, combat $H_{\text{crit}}$ damping | High near-miss clustering (>20%) | Remove rigged reveal slowdowns; disclose DDA |
| **Zeigarnik & FoMO** | Battle Pass, streaks, energy timers | Daily decay penalties, push reminders | Layer 5: Notification & Zeigarnik Hygiene |
| **Dual Currency** | Soft/Hard shop pricing | Remainder mismatch, 1-click checkout | Layer 4: Economic Isolation & real-cost display |
