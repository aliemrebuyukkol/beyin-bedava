# Mathematical Models & Algorithms (EOMM, Commercial Matchmaking, DDA)

Exact formulations, variables, empirical benchmarks, and engine-agnostic implementation patterns from Sections 2.1–2.3, 4.1, and 5 of *Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma*.

---

## 1. Skill-Based Matchmaking (SBMM)

Traditional SBMM uses Elo or Glicko-2 ratings to keep match win probability near 50%:

$$P(\text{Win}_{A \text{ vs } B}) = \frac{1}{1 + 10^{(R_B - R_A)/400}}$$

In pairwise pool matching, SBMM minimizes the fairness cost:

$$\text{cost}_{\text{SBMM}}(u, v) = |P(\text{Win}_{u \text{ vs } v}) - 0.50|$$

**Empirical limitation (Chen et al., 2017):** Pure fairness does not maximize player retention compared to sequence-aware engagement optimization.

---

## 2. Engagement Optimized Matchmaking (EOMM — Chen et al., 2017)

EOMM frames matchmaking as a **Graph Matching** and **Markov Decision Process (MDP)** problem to maximize total expected continuation across the player pool:

$$\max_X \sum_{i=1}^{N} \sum_{j \in M_i} E[R_i \mid s_i, o_{ij}] \cdot x_{ij}$$

where:
- $s_i$: player $i$'s current state vector (recent match W/L sequence, session duration, network latency).
- $o_{ij}$: predicted outcome distribution when pairing player $i$ with opponent/match $j$.
- $E[R_i \mid s_i, o_{ij}]$: expected retention / continuation probability into the next match.
- $x_{ij} \in \{0, 1\}$: assignment decision variable.

### Churn Risk Model

$$P(\text{Churn}_i \mid s_i, o) = \sigma(w^T \phi(s_i, o) + b), \quad \sigma(z) = \frac{1}{1 + e^{-z}}$$

Empirical behavioral findings:
- **Consecutive losses (`L-L-L`)** drive churn risk to its peak.
- **Alternating win-loss patterns (`W-L-W`)** yield the highest ongoing retention.

### Graph Matching / Linear Sum Assignment Formulation

Model the active lobby pool as a complete graph $G = (V, E)$. Each edge $(u, v)$ carries expected combined churn cost $w_{uv}$:

$$w_{uv} = E[\text{Churn}_u \mid s_u, P(\text{Win}_{uv})] + E[\text{Churn}_v \mid s_v, 1 - P(\text{Win}_{uv})]$$

where:

$$E[\text{Churn}_u \mid s_u, p] = p \cdot P(\text{Churn}_u \mid s_u, W) + (1 - p) \cdot P(\text{Churn}_u \mid s_u, L)$$

Solve for minimum total churn risk via **Minimum Weight Perfect Matching** or **Linear Sum Assignment** (`scipy.optimize.linear_sum_assignment` on the pool cost matrix).

### Pseudocode (EOMM Pool Matcher)

```text
function match_pool_eomm(players):
  N = len(players)
  cost_matrix = matrix(N, N, INF)
  for u in 0..N-1:
    for v in 0..N-1:
      if u == v: continue
      p_win_u = elo_win_prob(players[u].skill, players[v].skill)
      churn_u = p_win_u * churn_if(players[u].state, WIN) + (1 - p_win_u) * churn_if(players[u].state, LOSS)
      churn_v = (1 - p_win_u) * churn_if(players[v].state, WIN) + p_win_u * churn_if(players[v].state, LOSS)
      cost_matrix[u][v] = churn_u + churn_v
  pairs = linear_sum_assignment(cost_matrix)
  return deduplicate_undirected_pairs(pairs)
```

---

## 3. Commercial Conversion-Oriented Matchmaking (Activision US20170251672A1, Marr et al., 2017)

Combines matchmaking suitability directly with microtransaction conversion propensity:

$$S(m) = \alpha \cdot f_{\text{latency}}(m) + \beta \cdot f_{\text{skill}}(m) + \gamma \cdot f_{\text{monetization}}(m) + \delta \cdot f_{\text{social}}(m)$$

Key patent mechanisms:
1. **Player Profiling:**
   - **Marquee Player:** Veteran player equipped with rare cosmetics and advanced gear.
   - **Junior Player:** Non-spending or newer target player showing interest in a weapon/item class.
2. **Social Proof Pairing:** When a Junior Player browses or hovers over an item class, match them with a Marquee Player using that item's special skin/loadout so superior performance motivates purchase.
3. **Post-Purchase Reinforcement:** Immediately after purchase, temporarily relax $\beta$ (skill constraint) and place the player in a map/matchup where the new item holds statistical advantage against lower-skilled opponents—conditioning the purchase action with high victory satisfaction.

> **Mandatory Integration & Ethics Guardrail:** Unless the user explicitly builds an academic/audit simulation, keep `gamma_monetization = 0.0` in live player matchmaking and never manipulate opponent skill post-purchase without explicit disclosure. Use this formula in `AUDIT` mode to detect commercial bias in existing matchmaking code.

---

## 4. Dynamic Difficulty Adjustment — DDA (EA US10857468B2, Activision US10561945B2; Xue et al., 2020; Hunicke, 2005)

Real-time server/engine scaling driven by a player's normalized **Struggle Index** and expected performance delta $\Delta S_i(t)$.

### 4.1 Dynamic Hitbox Scaling

$$r_{\text{effective}}(t) = r_{\text{base}} \cdot \big(1 + \lambda \cdot \Delta S_i(t)\big)$$

- $r_{\text{base}}$: nominal collision/hitbox radius.
- $\Delta S_i(t)$: positive deviation when observed hit/success rate falls below expected baseline.
- $\lambda$: scaling sensitivity kept below the visual perception threshold (benchmark ceiling: `1.25x` when struggle index > `0.50`).

### 4.2 Bullet Magnetism

Nudge raw projectile/aim vector $v_{\text{raw}}$ toward target center vector $v_{\text{target}}$ by DDA intervention weight $w_{\text{dda}} \in [0, w_{\max}]$:

$$v_{\text{assisted}} = \text{normalize}\big((1 - w_{\text{dda}}) \cdot \hat{v}_{\text{raw}} + w_{\text{dda}} \cdot \hat{v}_{\text{target}}\big)$$

### 4.3 Hidden Damage Scaling & Critical-HP Protection ("Last-Bullet Mercy")

$$D_{\text{net}} = D_{\text{base}} \cdot M_{\text{loc}} \cdot \Phi(S_{\text{attacker}}, S_{\text{defender}})$$

- $D_{\text{base}}$: base weapon/ability damage.
- $M_{\text{loc}}$: hit-location multiplier (e.g., headshot, weakspot).
- $\Phi(S_{\text{attacker}}, S_{\text{defender}})$: skill-differential scaling multiplier (benchmark ceiling: `1.18x` when struggle index > `0.50`).
- **Critical-HP Exponential Damping:** When player HP drops below $H_{\text{crit}}$, incoming damage is exponentially damped to engineer artificial "near-death survival" (*clutch*) moments:

$$D_{\text{incoming, eff}} = \begin{cases} D_{\text{incoming}} \cdot \exp\big(-k \cdot (H_{\text{crit}} - H_{\text{ratio}})\big) & \text{if } H_{\text{ratio}} < H_{\text{crit}} \\ D_{\text{incoming}} & \text{otherwise} \end{cases}$$

### Telemetry Trigger & Player Perception Matrix (Page 3 Reference)

| Algorithmic Layer | Manipulated Variable | Telemetry Trigger | Player Perception |
| :--- | :--- | :--- | :--- |
| **EOMM Matchmaking** | Opponent skill distribution & team composition | 2–3 consecutive losses or rising lobby wait time | *"After a bad streak, I finally showed my real skill."* |
| **Commercial Matchmaking** | Store visibility & map/opponent advantage ($\gamma$ weight) | Cursor hover over store item or recent purchase | *"The new weapon/skin seriously boosted my performance."* |
| **DDA Physics & Aim** | Hitbox radius ($r_{\text{effective}}$) & bullet spread cone | Consecutive missed shots & dropping K/D ratio | *"My reflexes are sharp today; every shot lands."* |
| **DDA Damage & HP** | Weapon damage multiplier ($\Phi$) & critical-HP damage damping | Risk of session ending earlier than historical average | *"Survived at 1% HP and turned the fight around."* |

---

## 5. Thesis Stochastic Simulation Benchmarks (Sections 4.1 & 5)

Reference baseline for validating `scripts/simulate_eomm_dda.py`:
- **Population:** $N = 1000$ synthetic players ($n_{\text{SBMM}} = 500$, $n_{\text{EOMM}} = 500$), skill $\sim \mathcal{N}(\mu = 50, \sigma = 15)$, 60-match loop.
- **Reported Simulation Outcomes:**
  - EOMM increased session duration by **+44.8%** vs SBMM.
  - Statistical significance: Mann-Whitney $U = 178420, p < .001$, Rank-Biserial $r = 0.43$; Welch's $t = 14.82, p < .001$, Cohen's $d = 0.94$ (large effect).
  - DDA benchmark: when struggle index exceeds `50%`, hitbox radius scales to `1.25x` and damage multiplier to `1.18x`, suppressing player quit propensity.
