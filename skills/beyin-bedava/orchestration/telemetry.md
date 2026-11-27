# Telemetry input and evidence

`scripts/audit_telemetry.py --demo --format json` prints a synthetic audit. For an input example, see the `DEMO_TELEMETRY` object in the script.

| Input group | Validation and missing data |
| --- | --- |
| Provenance | Set `provenance.kind` to `observed` or `synthetic` and `source` to a traceable reference. Caller declarations require independent source review. |
| Match and session series | Chronological `W` / `L` outcomes and finite positive session durations in minutes. A full report needs at least 30 outcomes, three sessions and a positive baseline. |
| DDA | Supply accuracy delta, damage multiplier and clutch rate. For metric flags, provide `dda_context.attempts` of at least 30, comparable cohorts and expected modifiers accounted for. Record those facts under `matched_cohorts` and `expected_modifier_accounted_for`. |
| Store | Supply explicit booleans and counts. Odds and restore checks are applicable only when `paid_random_rewards` or `restorable_purchases` is true respectively. |
| Ads | Include known event counts, explicit booleans, `interstitial_interval_samples` and average interval in seconds where any intervals were observed. The frequency screen requires ten observed intervals. |
| Exposure | Supply loot near-miss rate, daily variable-ratio pulls and explicit `zeigarnik_triggers` booleans. |

Omit unknown metrics or set them to null. Empty and undersized series leave coverage incomplete. The audit preserves review signals from known fields and leaves the composite score null if coverage is incomplete. It never imputes unknown purchase, gameplay or advertising events as observed zeros. The score is a heuristic exposure index and carries no clinical or causal interpretation.

The rebound screen requires 60 matches, 20 opportunities and a 15 percentage-point lift before computing a permutation p-value. It conditions on the overall win rate by shuffling outcomes, using 999 deterministic draws and a one-sided 0.01 threshold. The exchangeable-history baseline is a screen. Check season boundaries, rank changes, player improvement and matchmaking configuration before drawing conclusions. Validate instrumentation and compare cohorts before escalating DDA, ads or store findings.
