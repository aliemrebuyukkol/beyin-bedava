#!/usr/bin/env python3
"""Replicated synthetic matchmaking scenarios and independent DDA bounds."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

def sigmoid(z: float) -> float:
    z = max(-30.0, min(30.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def elo_win_prob(skill_a: float, skill_b: float, scale: float = 6.0) -> float:
    """Logistic win probability calibrated for N(50, 15) skill spread."""
    return sigmoid((skill_a - skill_b) / scale)


def churn_probability(history: List[str], next_outcome: str, matches_played: int) -> float:
    """Assumed scenario parameters, without calibration to human data."""
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


def minimum_cost_assignment(costs: List[List[float]]) -> List[Tuple[int, int]]:
    """Hungarian assignment for a square matrix, with deterministic tie ordering."""
    size = len(costs)
    if any(len(row) != size or any(not math.isfinite(cost) for cost in row) for row in costs):
        raise ValueError("expected a square, finite cost matrix")
    row_potential = [0.0] * (size + 1)
    column_potential = [0.0] * (size + 1)
    assigned_row = [0] * (size + 1)
    parent = [0] * (size + 1)
    for new_row in range(1, size + 1):
        assigned_row[0] = new_row
        column = 0
        visited = [False] * (size + 1)
        slack = [math.inf] * (size + 1)
        while True:
            visited[column] = True
            row = assigned_row[column]
            step, next_column = math.inf, 0
            for candidate in range(1, size + 1):
                if visited[candidate]:
                    continue
                reduced = costs[row - 1][candidate - 1] - row_potential[row] - column_potential[candidate]
                if reduced < slack[candidate]:
                    slack[candidate], parent[candidate] = reduced, column
                if slack[candidate] < step:
                    step, next_column = slack[candidate], candidate
            for candidate in range(size + 1):
                if visited[candidate]:
                    row_potential[assigned_row[candidate]] += step
                    column_potential[candidate] -= step
                else:
                    slack[candidate] -= step
            column = next_column
            if assigned_row[column] == 0:
                break
        while column:
            previous = parent[column]
            assigned_row[column] = assigned_row[previous]
            column = previous
    return sorted((assigned_row[column] - 1, column - 1) for column in range(1, size + 1))


def pair_pool(pool: List[SyntheticPlayer], mode: str) -> List[Tuple[SyntheticPlayer, SyntheticPlayer]]:
    """Pair players in a lobby pool using adjacent SBMM or minimum-cost synthetic pairing."""
    if len(pool) < 2:
        return []

    ordered = sorted(pool, key=lambda p: p.skill)
    if len(ordered) % 2 == 1:
        # Caller shuffles pool each round, so the bye is not tied to skill.
        bye = pool[-1]
        ordered = [p for p in ordered if p is not bye]

    group_a = ordered[0::2]
    group_b = ordered[1::2]
    if mode == "sbmm":
        return list(zip(group_a, group_b))
    if mode != "eomm":
        raise ValueError("unknown synthetic pairing policy")
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
    pairs = minimum_cost_assignment(cost_matrix)
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


def compute_statistics(sbmm: List[int], eomm: List[int]) -> dict:
    """Descriptive effects only. Outcomes within each lobby share dependencies."""
    if not sbmm or len(sbmm) != len(eomm):
        raise ValueError("expected two nonempty, equally sized cohorts")
    n = len(sbmm)
    mean_s, mean_e = statistics.mean(sbmm), statistics.mean(eomm)
    counts_s, counts_e = Counter(sbmm), Counter(eomm)
    u, lower = 0.0, 0
    for count in sorted(counts_s.keys() | counts_e.keys()):
        u += counts_e[count] * (lower + counts_s[count] / 2)
        lower += counts_s[count]
    pooled_sd = math.sqrt((statistics.variance(sbmm) + statistics.variance(eomm)) / 2) if n > 1 else 0
    return {
        "n_per_group": n,
        "sbmm_mean_matches": mean_s,
        "sbmm_median_matches": statistics.median(sbmm),
        "eomm_mean_matches": mean_e,
        "eomm_median_matches": statistics.median(eomm),
        "session_uplift_pct": (mean_e - mean_s) / mean_s * 100 if mean_s else None,
        "mann_whitney_u": u,
        "mann_whitney_p": None,
        "rank_biserial_r": 2 * u / n**2 - 1,
        "welch_t": None,
        "welch_p": None,
        "cohens_d": (mean_e - mean_s) / pooled_sd if pooled_sd else None,
    }


def run_experiment(players, rounds, pool, seed, replicates):
    seeds = random.Random(seed)
    all_sbmm, all_eomm, differences, pairs = [], [], [], []
    for _ in range(replicates):
        cohort_seed = seeds.getrandbits(64)
        sbmm = simulate_group(players, rounds, pool, "sbmm", random.Random(cohort_seed))
        eomm = simulate_group(players, rounds, pool, "eomm", random.Random(cohort_seed))
        difference = statistics.mean(eomm) - statistics.mean(sbmm)
        differences.append(difference)
        pairs.append({"seed": cohort_seed, "mean_difference_matches": difference})
        all_sbmm.extend(sbmm)
        all_eomm.extend(eomm)
    bootstrap = random.Random(seeds.getrandbits(64))
    samples = sorted(statistics.mean(bootstrap.choices(differences, k=replicates)) for _ in range(2000))
    stats = compute_statistics(all_sbmm, all_eomm)
    stats.update(n_per_group=players, total_per_policy=len(all_sbmm),
                 mean_difference_matches=statistics.mean(differences),
                 paired_bootstrap_95_interval_matches=[samples[49], samples[1949]],
                 reached_round_cap_fraction={
                     "sbmm": all_sbmm.count(rounds) / len(all_sbmm),
                     "eomm": all_eomm.count(rounds) / len(all_eomm),
                 }, replicates=pairs)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate SBMM vs EOMM session retention and DDA bounds.")
    parser.add_argument("--players", type=int, default=1000, help="Total synthetic players (split 50/50).")
    parser.add_argument("--matches", type=int, default=60, help="Maximum match rounds simulated.")
    parser.add_argument("--pool-size", type=int, default=100, help="Lobby pool size per assignment tick.")
    parser.add_argument("--dda-struggle-threshold", type=float, default=0.50, help="DDA activation threshold.")
    parser.add_argument("--max-hitbox", type=float, default=1.25, help="Max DDA hitbox radius multiplier.")
    parser.add_argument("--max-damage", type=float, default=1.18, help="Max DDA damage multiplier.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--replicates", type=int, default=20, help="Independent paired cohorts, minimum 10.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text summary.")
    args = parser.parse_args()

    if args.players < 20 or args.players % 2 or args.matches < 1 or args.pool_size < 2:
        parser.error("players must be even and >=20; matches >=1; pool-size >=2")
    if not 0 <= args.dda_struggle_threshold <= 1 or not 1 <= args.max_hitbox <= 1.25 or not 1 <= args.max_damage <= 1.18:
        parser.error("DDA parameters outside documented bounds")
    if args.replicates < 10:
        parser.error("at least 10 paired cohorts are required")
    stats = run_experiment(args.players // 2, args.matches, args.pool_size, args.seed, args.replicates)
    dda = compute_dda_profile(
        struggle_threshold=args.dda_struggle_threshold,
        max_hitbox=args.max_hitbox,
        max_damage=args.max_damage,
    )
    payload = {"provenance": {"kind": "synthetic", "generator": "simulate_eomm_dda",
                              "seed": args.seed, "human_data": False},
               "simulation": stats, "dda": dda, "scipy_enabled": False,
               "design": {"players_per_cohort_per_policy": args.players // 2, "rounds": args.matches,
                          "pool_size": args.pool_size, "paired_cohorts": args.replicates,
                          "bootstrap_draws": 2000, "assignment": "adjacent_sbmm_vs_minimum_cost_eomm"},
               "limitations": ["Assumed churn weights with no empirical calibration.",
                               "Endpoint is restricted match count, bounded by the round horizon.",
                               "Bootstrap resamples independent paired cohorts and quantifies model variability only.",
                               "DDA curve is independent of the matchmaking simulation."]}

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("=== Synthetic EOMM vs SBMM model (not empirical player evidence) ===")
    print("DDA profile is independent; session length is match count.")
    print(f"Players/group: {stats['n_per_group']} | Max matches: {args.matches} | Pool size: {args.pool_size}")
    print(f"SBMM mean/median matches: {stats['sbmm_mean_matches']} / {stats['sbmm_median_matches']}")
    print(f"EOMM mean/median matches: {stats['eomm_mean_matches']} / {stats['eomm_median_matches']}")
    print(f"Paired mean difference: {stats['mean_difference_matches']:+.3f} matches")
    print(f"95% paired bootstrap interval: {stats['paired_bootstrap_95_interval_matches']}")
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
