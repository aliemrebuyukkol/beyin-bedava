#!/usr/bin/env python3
"""Stochastic EOMM vs SBMM & DDA Validation Simulator.

Implements the computational simulation model from Sections 4.1 and 5 of:
"Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma"

Uses scipy (linear_sum_assignment, mannwhitneyu, ttest_ind) when available,
with pure-stdlib fallbacks for zero-dependency portability.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from scipy.stats import mannwhitneyu, ttest_ind
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def sigmoid(z: float) -> float:
    z = max(-30.0, min(30.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def elo_win_prob(skill_a: float, skill_b: float, scale: float = 6.0) -> float:
    """Logistic win probability calibrated for N(50, 15) skill spread."""
    return sigmoid((skill_a - skill_b) / scale)


def churn_probability(history: List[str], next_outcome: str, matches_played: int) -> float:
    """Empirical churn risk model P(Churn | s_i, o) = sigma(w^T phi(s_i, o) + b).

    Captures EA EOMM findings:
    - L-L-L drives churn risk to peak (~45-55%).
    - W-L-W yields lowest churn risk (~2-3%, highest retention).
    - Single loss after wins (W-W-L / W-L) keeps churn low (~3-4%).
    """
    seq = (history + [next_outcome])[-3:]
    pattern = "".join(seq)

    pattern_weights: Dict[str, float] = {
        "LLL": 0.10,
        "LL": -1.35,
        "WLL": -1.25,
        "LWL": -2.75,
        "WLW": -3.80,
        "LWW": -3.30,
        "WWL": -3.10,
        "WWW": -2.40,
        "WL": -3.20,
        "LW": -3.40,
        "WW": -2.90,
        "L": -2.70,
        "W": -3.50,
    }
    base_logit = pattern_weights.get(pattern, -3.00)
    fatigue_term = 0.012 * matches_played
    return sigmoid(base_logit + fatigue_term)


@dataclass
class SyntheticPlayer:
    player_id: int
    skill: float
    history: List[str] = field(default_factory=list)
    matches_played: int = 0
    active: bool = True


def _greedy_bipartite_match(cost_matrix: List[List[float]]) -> List[Tuple[int, int]]:
    n = len(cost_matrix)
    edges = []
    for i in range(n):
        for j in range(n):
            edges.append((cost_matrix[i][j], i, j))
    edges.sort(key=lambda x: x[0])
    used_a, used_b = set(), set()
    pairs: List[Tuple[int, int]] = []
    for _, i, j in edges:
        if i not in used_a and j not in used_b:
            used_a.add(i)
            used_b.add(j)
            pairs.append((i, j))
            if len(pairs) == n:
                break
    return pairs


def pair_pool(pool: List[SyntheticPlayer], mode: str) -> List[Tuple[SyntheticPlayer, SyntheticPlayer]]:
    """Pair players in a lobby pool using SBMM or EOMM Linear Sum Assignment."""
    if len(pool) < 2:
        return []

    ordered = sorted(pool, key=lambda p: p.skill)
    if len(ordered) % 2 == 1:
        ordered = ordered[:-1]

    group_a = ordered[0::2]
    group_b = ordered[1::2]
    n = len(group_a)

    if mode == "sbmm":
        # Adjacent sorted skills minimize |P(Win) - 0.50|
        cost_matrix = [
            [abs(elo_win_prob(a.skill, b.skill) - 0.50) for b in group_b]
            for a in group_a
        ]
    else:
        cost_matrix = []
        for a in group_a:
            row = []
            for b in group_b:
                p_a = elo_win_prob(a.skill, b.skill)
                churn_a = (
                    p_a * churn_probability(a.history, "W", a.matches_played)
                    + (1.0 - p_a) * churn_probability(a.history, "L", a.matches_played)
                )
                churn_b = (
                    (1.0 - p_a) * churn_probability(b.history, "W", b.matches_played)
                    + p_a * churn_probability(b.history, "L", b.matches_played)
                )
                row.append(churn_a + churn_b)
            cost_matrix.append(row)

    if HAS_SCIPY:
        row_ind, col_ind = linear_sum_assignment(np.array(cost_matrix))
        return [(group_a[i], group_b[j]) for i, j in zip(row_ind, col_ind)]
    pairs = _greedy_bipartite_match(cost_matrix)
    return [(group_a[i], group_b[j]) for i, j in pairs]


def simulate_group(
    n_players: int,
    max_matches: int,
    pool_size: int,
    mode: str,
    rng: random.Random,
) -> List[int]:
    players = [
        SyntheticPlayer(
            player_id=i,
            skill=max(5.0, min(95.0, rng.gauss(50.0, 15.0))),
        )
        for i in range(n_players)
    ]

    for _ in range(max_matches):
        active = [p for p in players if p.active]
        if len(active) < 2:
            break
        rng.shuffle(active)
        for start in range(0, len(active), pool_size):
            chunk = active[start : start + pool_size]
            for p_a, p_b in pair_pool(chunk, mode):
                p_win_a = elo_win_prob(p_a.skill, p_b.skill)
                a_wins = rng.random() < p_win_a
                out_a = "W" if a_wins else "L"
                out_b = "L" if a_wins else "W"

                for player, outcome in ((p_a, out_a), (p_b, out_b)):
                    player.matches_played += 1
                    p_churn = churn_probability(player.history, outcome, player.matches_played)
                    player.history.append(outcome)
                    if rng.random() < p_churn:
                        player.active = False

    return [p.matches_played for p in players]


def compute_dda_profile(
    struggle_threshold: float = 0.50,
    max_hitbox: float = 1.25,
    max_damage: float = 1.18,
    max_magnetism: float = 0.25,
    h_crit: float = 0.15,
    damping_rate: float = 3.0,
) -> Dict[str, object]:
    """Compute bounded DDA scaling curve across struggle index [0.0, 1.0]."""
    sample_points = [0.0, 0.25, 0.50, 0.75, 1.0]
    curve = []
    for s in sample_points:
        if s <= struggle_threshold:
            norm = 0.0
        else:
            norm = (s - struggle_threshold) / max(1e-6, 1.0 - struggle_threshold)
        hitbox_mult = 1.0 + (max_hitbox - 1.0) * norm
        damage_mult = 1.0 + (max_damage - 1.0) * norm
        magnetism = max_magnetism * norm
        curve.append({
            "struggle_index": round(s, 2),
            "hitbox_multiplier": round(hitbox_mult, 3),
            "damage_multiplier": round(damage_mult, 3),
            "bullet_magnetism": round(magnetism, 3),
        })

    # Critical HP damping check at 5% HP
    hp_ratio = 0.05
    crit_damping = math.exp(-damping_rate * max(0.0, h_crit - hp_ratio))
    return {
        "struggle_threshold": struggle_threshold,
        "curve": curve,
        "critical_hp_threshold": h_crit,
        "incoming_damage_factor_at_5pct_hp": round(crit_damping, 3),
    }


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def compute_statistics(sbmm: List[int], eomm: List[int]) -> Dict[str, Optional[float]]:
    n1, n2 = len(sbmm), len(eomm)
    mean_s, mean_e = statistics.mean(sbmm), statistics.mean(eomm)
    med_s, med_e = statistics.median(sbmm), statistics.median(eomm)
    uplift_pct = ((mean_e - mean_s) / mean_s * 100.0) if mean_s > 0 else 0.0

    var_s = statistics.variance(sbmm) if n1 > 1 else 0.0
    var_e = statistics.variance(eomm) if n2 > 1 else 0.0
    pooled_sd = math.sqrt(((n1 - 1) * var_s + (n2 - 1) * var_e) / max(1, n1 + n2 - 2))
    cohens_d = (mean_e - mean_s) / pooled_sd if pooled_sd > 0 else 0.0

    if HAS_SCIPY:
        u_stat, u_p = mannwhitneyu(eomm, sbmm, alternative="two-sided")
        t_stat, t_p = ttest_ind(eomm, sbmm, equal_var=False)
        u_val = float(u_stat)
        u_p_val = float(u_p)
        t_val = float(t_stat)
        t_p_val = float(t_p)
    else:
        # Pure-stdlib normal-approximation fallback
        se = math.sqrt(var_s / n1 + var_e / n2) if (var_s + var_e) > 0 else 1.0
        t_val = (mean_e - mean_s) / se
        t_p_val = 2.0 * (1.0 - _normal_cdf(abs(t_val)))
        u_val = sum((1.0 if e > s else (0.5 if e == s else 0.0)) for e in eomm for s in sbmm)
        mu_u = n1 * n2 / 2.0
        sigma_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
        z_u = (u_val - mu_u) / sigma_u if sigma_u > 0 else 0.0
        u_p_val = 2.0 * (1.0 - _normal_cdf(abs(z_u)))

    rank_biserial_r = (2.0 * u_val) / (n1 * n2) - 1.0
    return {
        "n_per_group": n1,
        "sbmm_mean_matches": round(mean_s, 2),
        "sbmm_median_matches": round(med_s, 2),
        "eomm_mean_matches": round(mean_e, 2),
        "eomm_median_matches": round(med_e, 2),
        "session_uplift_pct": round(uplift_pct, 2),
        "mann_whitney_u": round(u_val, 1),
        "mann_whitney_p": round(u_p_val, 6),
        "rank_biserial_r": round(rank_biserial_r, 3),
        "welch_t": round(t_val, 3),
        "welch_p": round(t_p_val, 6),
        "cohens_d": round(cohens_d, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate SBMM vs EOMM session retention and DDA bounds.")
    parser.add_argument("--players", type=int, default=1000, help="Total synthetic players (split 50/50).")
    parser.add_argument("--matches", type=int, default=60, help="Maximum match rounds simulated.")
    parser.add_argument("--pool-size", type=int, default=100, help="Lobby pool size per assignment tick.")
    parser.add_argument("--dda-struggle-threshold", type=float, default=0.50, help="DDA activation threshold.")
    parser.add_argument("--max-hitbox", type=float, default=1.25, help="Max DDA hitbox radius multiplier.")
    parser.add_argument("--max-damage", type=float, default=1.18, help="Max DDA damage multiplier.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text summary.")
    args = parser.parse_args()

    n_per_group = max(10, args.players // 2)
    rng_sbmm = random.Random(args.seed)
    rng_eomm = random.Random(args.seed + 1)

    sbmm_sessions = simulate_group(n_per_group, args.matches, args.pool_size, "sbmm", rng_sbmm)
    eomm_sessions = simulate_group(n_per_group, args.matches, args.pool_size, "eomm", rng_eomm)

    stats = compute_statistics(sbmm_sessions, eomm_sessions)
    dda = compute_dda_profile(
        struggle_threshold=args.dda_struggle_threshold,
        max_hitbox=args.max_hitbox,
        max_damage=args.max_damage,
    )
    payload = {"simulation": stats, "dda": dda, "scipy_enabled": HAS_SCIPY}

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("=== EOMM vs SBMM Stochastic Simulation ===")
    print(f"Players/group: {stats['n_per_group']} | Max matches: {args.matches} | Pool size: {args.pool_size}")
    print(f"SBMM mean/median matches: {stats['sbmm_mean_matches']} / {stats['sbmm_median_matches']}")
    print(f"EOMM mean/median matches: {stats['eomm_mean_matches']} / {stats['eomm_median_matches']}")
    print(f"EOMM session uplift: +{stats['session_uplift_pct']}%")
    print(
        f"Mann-Whitney U = {stats['mann_whitney_u']} (p={stats['mann_whitney_p']}), "
        f"Rank-Biserial r = {stats['rank_biserial_r']}"
    )
    print(f"Welch's t = {stats['welch_t']} (p={stats['welch_p']}), Cohen's d = {stats['cohens_d']}")
    print("\n=== DDA Bounded Intervention Curve ===")
    for pt in dda["curve"]:
        print(
            f"Struggle {pt['struggle_index']:.2f} -> Hitbox {pt['hitbox_multiplier']}x | "
            f"Damage {pt['damage_multiplier']}x | Magnetism {pt['bullet_magnetism']}"
        )
    print(
        f"Critical-HP (<={dda['critical_hp_threshold']*100:.0f}%) incoming damage factor at 5% HP: "
        f"{dda['incoming_damage_factor_at_5pct_hp']}x"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
