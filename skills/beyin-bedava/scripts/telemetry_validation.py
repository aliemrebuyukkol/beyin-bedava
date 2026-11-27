"""Validate fields consumed by the audit without imputing missing observations."""
from __future__ import annotations

import math
import random

MAX_COUNT = 2**53 - 1
COUNTS = {
    "daily_variable_ratio_pulls", "economy.fomo_timed_offers_count",
    "economy.impulsive_purchases_last_7d", "ads.mid_gameplay_interstitial_count",
    "ads.interstitial_after_loss_streak_count", "ads.interstitial_interval_samples",
    "dda_context.attempts",
}
RANGES = {
    "accuracy_during_struggle_delta": (-1, 1), "damage_multiplier_observed": (0, 1000),
    "critical_hp_clutch_rate": (0, 1), "loot_near_miss_rate": (0, 1),
    "baseline_session_minutes": (0, 1440), "ads.avg_interstitial_interval_seconds": (0, 86400),
}
BOOL = {
    "economy.dual_currency", "economy.bundle_price_mismatch", "economy.one_click_checkout",
    "economy.real_money_equivalent_shown", "economy.fake_resetting_timers",
    "economy.odds_disclosed", "economy.restore_purchases_present", "economy.post_purchase_mmr_drop",
    "economy.paid_random_rewards", "economy.restorable_purchases",
    "ads.banner_cta_overlap", "ads.dda_rigged_for_rewarded_revive",
    "zeigarnik_triggers.expiring_battle_pass", "zeigarnik_triggers.punitive_daily_streak",
    "zeigarnik_triggers.energy_bar_notifications", "dda_context.matched_cohorts",
    "dda_context.expected_modifier_accounted_for",
}
OPTIONAL = {"dda_context.attempts", "dda_context.matched_cohorts", "dda_context.expected_modifier_accounted_for"}


def is_number(value, low, high):
    return type(value) in (float, int) and low <= value <= high and math.isfinite(value)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("expected a telemetry object")
    errors, missing = [], []
    for key in ("economy", "ads", "zeigarnik_triggers", "provenance", "dda_context"):
        if key in data and not isinstance(data[key], dict):
            errors.append(f"{key}: expected object")
    if errors:
        return errors, missing
    provenance = data.get("provenance")
    if provenance is None:
        missing.append("provenance")
    elif (provenance.get("kind") not in ("observed", "synthetic")
          or not isinstance(provenance.get("source"), str) or not provenance["source"].strip()):
        errors.append("provenance: declare kind (observed or synthetic) and source")
    if "player_id" in data and not isinstance(data["player_id"], str):
        errors.append("player_id: expected a string")
    for field, predicate in (
        ("match_history", lambda value: isinstance(value, list) and all(x in ("W", "L") for x in value)),
        ("session_durations_minutes", lambda value: isinstance(value, list)
         and all(is_number(x, 0, 1440) and x > 0 for x in value)),
    ):
        if data.get(field) is None:
            missing.append(field)
        elif not predicate(data[field]):
            errors.append(f"{field}: invalid observations")
        elif len(data[field]) < (30 if field == "match_history" else 3):
            missing.append(f"{field}: insufficient observations")
    for field in sorted(COUNTS | RANGES.keys() | BOOL):
        parent, separator, name = field.partition(".")
        value = data.get(parent, {}).get(name) if separator else data.get(parent)
        if value is None:
            if field not in OPTIONAL:
                missing.append(field)
            continue
        if field in COUNTS:
            valid = type(value) is int and 0 <= value <= MAX_COUNT
        elif field in BOOL:
            valid = type(value) is bool
        else:
            valid = is_number(value, *RANGES[field])
            if field in {"baseline_session_minutes", "damage_multiplier_observed",
                         "ads.avg_interstitial_interval_seconds"}:
                valid = valid and value > 0
        if not valid:
            errors.append(f"{field}: invalid value or type")
    ads = data.get("ads", {})
    if not errors and ads.get("interstitial_interval_samples") == 0:
        if ads.get("avg_interstitial_interval_seconds") is not None:
            errors.append("interstitial interval average requires interval observations")
        else:
            missing.remove("ads.avg_interstitial_interval_seconds")
    economy = data.get("economy", {})
    for applicability, observation in (("paid_random_rewards", "odds_disclosed"),
                                       ("restorable_purchases", "restore_purchases_present")):
        field = f"economy.{observation}"
        if economy.get(applicability) is False and field in missing:
            missing.remove(field)
    return errors, missing


def rebound_test(history):
    """One-sided permutation screen under exchangeability, conditional on overall wins."""
    def counts(sequence):
        windows = wins = loss_run = 0
        for outcome in sequence:
            if loss_run >= 2:
                windows += 1
                wins += outcome == "W"
            loss_run = loss_run + 1 if outcome == "L" else 0
        return windows, wins

    opportunities, wins = counts(history)
    result = {"opportunities": opportunities, "status": "insufficient", "p_value": None}
    if opportunities < 20 or len(history) < 60:
        return result
    baseline = history.count("W") / len(history)
    delta = wins / opportunities - baseline
    result.update(status="no_signal", baseline_win_rate=baseline, rebound_lift=delta)
    if delta < 0.15:
        return result
    rng = random.Random(42)
    shuffled = list(history)
    exceed = 0
    for _ in range(999):
        rng.shuffle(shuffled)
        windows, post_loss_wins = counts(shuffled)
        exceed += windows > 0 and post_loss_wins / windows - baseline >= delta
    p_value = (exceed + 1) / 1000
    result.update(status="signal" if p_value <= 0.01 else "no_signal", p_value=p_value)
    return result
