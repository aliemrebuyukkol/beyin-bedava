#!/usr/bin/env python3
"""4-Stage Autonomous Telemetry, Ads, Store/IAP & Dark Pattern Auditor.

Implements Section 6.1 of:
"Algoritmik Etkileşim Mimarisi ve Davranışsal Şartlanma":
  1. Telemetry & Pattern Diagnosis
  2. Algorithmic Classification (EOMM, DDA, Economy/IAP & Ad Dark Patterns)
  3. Neurobiological Risk Scoring (LOW / MEDIUM / HIGH)
  4. 5-Layer Friction Protocol & Monetization Remediation Assignment
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from telemetry_validation import rebound_test, validate


DEMO_TELEMETRY: Dict[str, Any] = {
    "player_id": "demo_player_01",
    "provenance": {"kind": "synthetic", "source": "built-in demonstration"},
    "match_history": [
        "W", "L", "L", "W", "L", "L", "W", "L", "W", "L",
        "L", "W", "W", "L", "L", "W", "L", "W", "L", "L", "W",
        "W", "L", "L", "W", "L", "W", "W", "L", "W",
    ],
    "session_durations_minutes": [42, 58, 76, 94, 112, 128],
    "baseline_session_minutes": 45.0,
    "accuracy_during_struggle_delta": 0.21,
    "damage_multiplier_observed": 1.18,
    "critical_hp_clutch_rate": 0.31,
    "loot_near_miss_rate": 0.28,
    "daily_variable_ratio_pulls": 14,
    "economy": {
        "dual_currency": True,
        "bundle_price_mismatch": True,
        "one_click_checkout": True,
        "fomo_timed_offers_count": 4,
        "impulsive_purchases_last_7d": 3,
        "real_money_equivalent_shown": False,
        "fake_resetting_timers": True,
        "paid_random_rewards": True,
        "odds_disclosed": False,
        "restorable_purchases": True,
        "restore_purchases_present": False,
        "post_purchase_mmr_drop": True,
    },
    "ads": {
        "mid_gameplay_interstitial_count": 2,
        "interstitial_after_loss_streak_count": 3,
        "avg_interstitial_interval_seconds": 65,
        "interstitial_interval_samples": 12,
        "banner_cta_overlap": True,
        "dda_rigged_for_rewarded_revive": True,
    },
    "zeigarnik_triggers": {
        "expiring_battle_pass": True,
        "punitive_daily_streak": True,
        "energy_bar_notifications": True,
    },
}


def stage1_diagnose(data: Dict[str, Any]) -> Dict[str, Any]:
    history: List[str] = data.get("match_history", [])
    total = len(history)
    wins = sum(1 for m in history if m == "W")
    losses = sum(1 for m in history if m == "L")

    max_loss_streak = 0
    cur_loss = 0
    post_2loss_opportunities = 0
    post_2loss_wins = 0

    for outcome in history:
        if cur_loss >= 2:
            post_2loss_opportunities += 1
            if outcome == "W":
                post_2loss_wins += 1
        if outcome == "L":
            cur_loss += 1
            max_loss_streak = max(max_loss_streak, cur_loss)
        else:
            cur_loss = 0

    rebound_rate = (post_2loss_wins / post_2loss_opportunities) if post_2loss_opportunities else 0.0
    wlw_count = sum(1 for i in range(len(history) - 2) if history[i : i + 3] == ["W", "L", "W"])
    lll_count = sum(1 for i in range(len(history) - 2) if history[i : i + 3] == ["L", "L", "L"])

    sessions = data.get("session_durations_minutes", [])
    baseline = float(data.get("baseline_session_minutes", 45.0)) or 45.0
    avg_session = sum(sessions) / len(sessions) if sessions else baseline
    session_ratio = avg_session / baseline

    ads = data.get("ads", {})

    return {
        "total_matches": total,
        "win_rate": round(wins / total, 3) if total else 0.0,
        "losses": losses,
        "max_consecutive_losses": max_loss_streak,
        "post_2loss_win_rebound_rate": round(rebound_rate, 3),
        "post_2loss_opportunities": post_2loss_opportunities,
        "wlw_triplets": wlw_count,
        "lll_triplets": lll_count,
        "avg_session_minutes": round(avg_session, 1),
        "baseline_session_minutes": baseline,
        "session_escalation_ratio": round(session_ratio, 2),
        "mid_gameplay_interstitials": int(ads.get("mid_gameplay_interstitial_count", 0)),
        "loss_streak_interstitials": int(ads.get("interstitial_after_loss_streak_count", 0)),
    }


def stage2_classify(data: Dict[str, Any], diag: Dict[str, Any]) -> Dict[str, Any]:
    rebound = rebound_test(data.get("match_history", []))
    eomm_signals = []
    if rebound["status"] == "signal":
        eomm_signals.append("Unusually high post-loss rebound under a shuffled-history baseline")

    dda_signals: List[str] = []
    acc_delta = float(data.get("accuracy_during_struggle_delta", 0.0))
    dmg_mult = float(data.get("damage_multiplier_observed", 1.0))
    clutch_rate = float(data.get("critical_hp_clutch_rate", 0.0))
    ads = data.get("ads", {})
    context = data.get("dda_context", {})
    comparable = (context.get("attempts", 0) >= 30 and context.get("matched_cohorts") is True
                  and context.get("expected_modifier_accounted_for") is True)
    if comparable and acc_delta >= 0.12:
        dda_signals.append(f"Struggle-phase hit accuracy jump (+{acc_delta*100:.1f}%)")
    if comparable and dmg_mult > 1.05:
        dda_signals.append(f"Unexpected damage multiplier ({dmg_mult:.2f}x)")
    if comparable and clutch_rate >= 0.20:
        dda_signals.append(f"Elevated critical-HP clutch survival clustering ({clutch_rate*100:.0f}%)")
    if ads.get("dda_rigged_for_rewarded_revive"):
        dda_signals.append("Reported DDA interference around rewarded-ad revives")

    econ = data.get("economy", {})
    zeig = data.get("zeigarnik_triggers", {})
    iap_dark_signals: List[str] = []
    if econ.get("dual_currency") and not econ.get("real_money_equivalent_shown", True):
        iap_dark_signals.append("Dual currency without real-money equivalent display")
    if econ.get("bundle_price_mismatch"):
        iap_dark_signals.append("Store bundle-to-item price remainder mismatch")
    if econ.get("one_click_checkout"):
        iap_dark_signals.append("Review one-click checkout for informed consent")
    if econ.get("fake_resetting_timers"):
        iap_dark_signals.append("Fake resetting FoMO countdown timers in store")
    if econ.get("paid_random_rewards") is True and econ.get("odds_disclosed") is False:
        iap_dark_signals.append("Undisclosed loot/gacha drop odds")
    if econ.get("restorable_purchases") is True and econ.get("restore_purchases_present") is False:
        iap_dark_signals.append("Missing Restore Purchases control in store UI")
    if econ.get("post_purchase_mmr_drop"):
        iap_dark_signals.append("Reported post-purchase MMR decline requiring cohort review")
    if int(econ.get("fomo_timed_offers_count", 0)) > 0:
        iap_dark_signals.append(f"Review active countdown offers ({econ.get('fomo_timed_offers_count')})")
    if zeig.get("punitive_daily_streak") or zeig.get("energy_bar_notifications"):
        iap_dark_signals.append("Zeigarnik streak/energy tension notifications")

    ad_dark_signals: List[str] = []
    if int(ads.get("mid_gameplay_interstitial_count", 0)) > 0:
        ad_dark_signals.append(
            f"Mid-gameplay interstitial interruptions ({ads.get('mid_gameplay_interstitial_count')})"
        )
    if int(ads.get("interstitial_after_loss_streak_count", 0)) > 0:
        ad_dark_signals.append(
            f"Interstitials triggered immediately after >=2 loss streaks ({ads.get('interstitial_after_loss_streak_count')})"
        )
    interval = ads.get("avg_interstitial_interval_seconds")
    if interval is not None and ads.get("interstitial_interval_samples", 0) >= 10 and interval < 120:
        ad_dark_signals.append(f"Excessive interstitial frequency (avg {interval}s < 120s)")
    if ads.get("banner_cta_overlap"):
        ad_dark_signals.append("Banner overlaps or crowds interactive CTAs (<16px margin)")

    return {
        "EOMM_detected": len(eomm_signals) > 0,
        "EOMM_evidence_status": "insufficient" if rebound["status"] == "insufficient" else "screening_only",
        "EOMM_rebound_screen": rebound,
        "DDA_evidence_status": "screening_only" if comparable else "insufficient",
        "EOMM_signals": eomm_signals,
        "DDA_detected": len(dda_signals) > 0,
        "DDA_signals": dda_signals,
        "DARK_PATTERN_detected": (len(iap_dark_signals) + len(ad_dark_signals)) > 0,
        "IAP_DARK_PATTERN_signals": iap_dark_signals,
        "AD_DARK_PATTERN_signals": ad_dark_signals,
    }


def stage3_risk_score(data: Dict[str, Any], diag: Dict[str, Any]) -> Dict[str, Any]:
    pulls = int(data.get("daily_variable_ratio_pulls", 0))
    var_ratio_pts = min(25, pulls * 1.5)

    near_miss = float(data.get("loot_near_miss_rate", 0.0))
    clutch = float(data.get("critical_hp_clutch_rate", 0.0))
    ads = data.get("ads", {})
    revive_rig = 5.0 if ads.get("dda_rigged_for_rewarded_revive") else 0.0
    rpe_pts = min(25, (near_miss * 45.0) + (clutch * 30.0) + revive_rig)

    zeig = data.get("zeigarnik_triggers", {})
    econ = data.get("economy", {})
    zeig_pts = min(
        25,
        (7 if zeig.get("expiring_battle_pass") else 0)
        + (6 if zeig.get("punitive_daily_streak") else 0)
        + (5 if zeig.get("energy_bar_notifications") else 0)
        + (4 if econ.get("fake_resetting_timers") else 0)
        + min(3, int(econ.get("fomo_timed_offers_count", 0))),
    )

    esc_ratio = diag["session_escalation_ratio"]
    impulses = int(econ.get("impulsive_purchases_last_7d", 0))
    ad_pressure = 3.0 if int(ads.get("interstitial_after_loss_streak_count", 0)) > 0 else 0.0
    esc_pts = min(25, max(0.0, (esc_ratio - 1.0) * 16.0) + impulses * 4.5 + ad_pressure)

    total_score = round(var_ratio_pts + rpe_pts + zeig_pts + esc_pts, 1)
    if total_score >= 67:
        tier = "HIGH"
    elif total_score >= 34:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return {
        "score": total_score,
        "tier": tier,
        "breakdown": {
            "variable_ratio_exposure_25": round(var_ratio_pts, 1),
            "rpe_and_near_miss_25": round(rpe_pts, 1),
            "zeigarnik_and_fomo_25": round(zeig_pts, 1),
            "session_escalation_and_spend_25": round(esc_pts, 1),
        },
    }


def stage4_assign_protocols(
    classification: Dict[str, Any], risk: Dict[str, Any]
) -> List[Dict[str, str]]:
    protocols: List[Dict[str, str]] = []
    tier = risk["tier"]

    if tier in ("MEDIUM", "HIGH") or classification["DDA_detected"]:
        protocols.append({
            "layer": "1. Visual Cortex Suppression",
            "action": "Enable Grayscale shader mode and cap display luminance at 40%.",
            "target": "Dampen phasic dopamine spikes from reward animations & rarity colors.",
        })
        protocols.append({
            "layer": "2. Cognitive Friction",
            "action": "Disable auto-requeue/auto-login; enforce 20s+ deliberate start countdown.",
            "target": "Interrupt habit automation and re-engage prefrontal control.",
        })

    if tier == "HIGH" or classification["EOMM_detected"]:
        protocols.append({
            "layer": "3. EOMM Loop Interruption (2-Loss Stop)",
            "action": "Offer an optional, dismissible break reminder after consecutive losses.",
            "target": "Support an optional break without changing match outcomes.",
        })

    if tier == "HIGH" or classification["IAP_DARK_PATTERN_signals"]:
        protocols.append({
            "layer": "4. Economic Isolation & Store Remediation",
            "action": "Require 2-step checkout, show real-money price, align currency packs, disclose odds, add Restore Purchases, offer optional purchase limits, and exclude purchase signals from matchmaking.",
            "target": "Restore Pain of Paying brake and eliminate store dark patterns.",
        })

    if classification["AD_DARK_PATTERN_signals"]:
        protocols.append({
            "layer": "Ad Placement Remediation",
            "action": "Move interstitials strictly to natural boundaries (>=180s & >=2 matches cooldown), suppress after 2+ losses, hide banners in gameplay (>=16px margin), and stop DDA revive rigging.",
            "target": "Eliminate tilt-driven forced ads and accidental-tap banner traps.",
        })

    if tier == "HIGH" or classification["DARK_PATTERN_detected"]:
        protocols.append({
            "layer": "5. Notification & Zeigarnik Hygiene",
            "action": "Suppress streak, energy-refill, and timed-event notifications; hide quest badges and remove fake resetting timers.",
            "target": "Eliminate artificial Zeigarnik cognitive tension.",
        })

    if not protocols:
        protocols.append({
            "layer": "Baseline Transparency",
            "action": "Maintain SBMM mode, boundary-safe ads, published drop odds, and optional well-being toggles.",
            "target": "Preserve low-risk autonomous play.",
        })
    return protocols


def render_markdown(report: Dict[str, Any]) -> str:
    s1 = report["stage_1_telemetry_diagnosis"]
    s2 = report["stage_2_algorithmic_classification"]
    s3 = report["stage_3_neurobiological_risk"]
    s4 = report["stage_4_friction_protocols"]

    lines = [
        f"# Beyin-Bedava 4-Stage Audit (`{report['player_id']}`)",
        "",
        "## 1. Telemetry & Pattern Diagnosis",
        f"- Matches analyzed: **{s1['total_matches']}** (Win rate: `{s1['win_rate']*100:.1f}%`, Max loss streak: `{s1['max_consecutive_losses']}`)",
        f"- Post-2-loss win rebound rate: **`{s1['post_2loss_win_rebound_rate']*100:.1f}%`** (`W-L-W` triplets: `{s1['wlw_triplets']}`, `L-L-L` triplets: `{s1['lll_triplets']}`)",
        f"- Session escalation: **`{s1['avg_session_minutes']}m`** vs baseline `{s1['baseline_session_minutes']}m` (`{s1['session_escalation_ratio']}x`)",
        f"- Ad anomalies: Mid-gameplay interstitials `{s1['mid_gameplay_interstitials']}`, Loss-streak interstitials `{s1['loss_streak_interstitials']}`",
        "",
        "## 2. Algorithmic Classification",
        f"- **EOMM:** `{s2['EOMM_detected']}` — {', '.join(s2['EOMM_signals']) or 'No strong signature'}",
        f"- **DDA:** `{s2['DDA_detected']}` — {', '.join(s2['DDA_signals']) or 'No strong signature'}",
        f"- **IAP/Economy Dark Patterns:** `{len(s2['IAP_DARK_PATTERN_signals']) > 0}` — {', '.join(s2['IAP_DARK_PATTERN_signals']) or 'None detected'}",
        f"- **Ad Dark Patterns:** `{len(s2['AD_DARK_PATTERN_signals']) > 0}` — {', '.join(s2['AD_DARK_PATTERN_signals']) or 'None detected'}",
        "",
        "## 3. Neurobiological Risk Score",
        f"- Composite Score: **`{s3['score']}/100` (`{s3['tier']}`)**",
        f"  - Variable Ratio Exposure: `{s3['breakdown']['variable_ratio_exposure_25']}/25`",
        f"  - RPE & Near-Miss Density: `{s3['breakdown']['rpe_and_near_miss_25']}/25`",
        f"  - Zeigarnik & FoMO Pressure: `{s3['breakdown']['zeigarnik_and_fomo_25']}/25`",
        f"  - Session Escalation & Spend: `{s3['breakdown']['session_escalation_and_spend_25']}/25`",
        "",
        "## 4. Assigned Protection, Ad & Store Remediation Protocols",
    ]
    for item in s4:
        lines.append(f"- **{item['layer']}:** {item['action']} *(Effect: {item['target']})*")
    lines.extend([
        "",
        "### 4-Week Evaluation KPIs (Section 4.2)",
        "- Weekly Playtime (telemetry hours/week) | Impulsive Microtransaction Count | Brief Self-Control Scale",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Beyin-Bedava 4-stage telemetry, ads & store audit.")
    parser.add_argument("--input", type=Path, help="Path to telemetry JSON file.")
    parser.add_argument("--demo", action="store_true", help="Run against built-in demo telemetry.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.demo == (args.input is not None):
        parser.error("Provide exactly one of --input or --demo")

    try:
        data = DEMO_TELEMETRY if args.demo else json.loads(args.input.read_text(encoding="utf-8"))
        errors, missing = validate(data)
    except (OSError, ValueError) as exc:
        errors, missing = [str(exc)], []
    if errors:
        if args.format == "json":
            print(json.dumps({"status": "invalid", "errors": errors, "missing": missing}, indent=2))
        else:
            print("Invalid telemetry: " + "; ".join(errors), file=sys.stderr)
        return 2
    data = {key: ({k: v for k, v in value.items() if v is not None} if isinstance(value, dict) else value)
            for key, value in data.items() if value is not None}
    s1 = stage1_diagnose(data)
    s2 = stage2_classify(data, s1)
    # Scores aggregate multiple dimensions and require complete coverage. Partial
    # inputs still expose observable policy concerns and the missing fields.
    s3 = stage3_risk_score(data, s1) if not missing else None
    s4 = stage4_assign_protocols(s2, s3) if s3 is not None else []
    provenance = data.get("provenance", {"kind": "unknown"})
    flagged = (s2["DARK_PATTERN_detected"] or s2["EOMM_detected"] or s2["DDA_detected"])
    coverage_gap = (missing or s2["EOMM_evidence_status"] == "insufficient"
                    or s2["DDA_evidence_status"] == "insufficient")
    status = "review_required" if flagged else "insufficient" if coverage_gap else (
        "synthetic_only" if provenance["kind"] == "synthetic" else "no_screening_signal")
    report = {
        "status": status, "provenance": provenance, "missing": missing,
        "interpretation": ("Heuristic screening with possible confounders such as rank drift, session boundaries "
                           "and intentional assists. Source is caller-declared. Synthetic results cannot support "
                           "conclusions about players."),
        "player_id": data.get("player_id", "unknown"),
        "stage_1_telemetry_diagnosis": s1 if not missing else None,
        "stage_2_algorithmic_classification": s2,
        "stage_3_neurobiological_risk": s3,
        "stage_4_friction_protocols": s4,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"Evidence: {provenance['kind']} | Status: {status}")
        if missing:
            print("Missing: " + ", ".join(missing))
            for key in ("EOMM_signals", "DDA_signals", "IAP_DARK_PATTERN_signals", "AD_DARK_PATTERN_signals"):
                for signal in s2[key]:
                    print(f"- {signal}")
        else:
            print(render_markdown(report))
    return 1 if flagged else 2 if coverage_gap or status == "synthetic_only" else 0


if __name__ == "__main__":
    sys.exit(main())
