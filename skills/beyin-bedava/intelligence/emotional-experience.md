# Emotional experience and human playtest criteria

Before play, record the emotion intended for one moment (for example relief immediately after escaping), competing interpretations and an acceptable distress threshold. Ask a neutral open-ended question at that moment, then use the same coding rubric for every participant. Let participants skip questions, abandon the test or use accessibility controls. Use aggregates with an opaque evidence reference.

Use `scripts/evaluate_experience.py` with a JSON plan declaring `threshold`, `min_samples`, `method` and `population` per criterion. Declare the unit of analysis in the method, and avoid treating repeated attempts by a participant as independent people. Observations provide `source`, `value`, `sample_size` and `reference`. Use independent evidence for the intended emotion and for distress.

| Area | Criterion | Operational definition |
| --- | --- | --- |
| Motivation | `meaningful_choice_rate` | Fraction of participants who can name two viable options and correctly distinguish one consequence. |
| Motivation | `voluntary_retry_rate` | Fraction of eligible failed players who choose retry after an equally visible, penalty-free exit. |
| Creative mechanics | `distinct_mechanic_alternatives` | Count alternatives that change the rules, decision or consequence after independent review. A reskin counts once. |
| Creative mechanics | `distinct_successful_strategies` | Count different tactics that reach the goal in agreed playtest scenarios. |
| Game feel | `input_feedback_p95_ms` | 95th percentile elapsed time from input event to first visible or audible acknowledgement, by device and mode. |
| Game feel | `missed_input_rate` | Fraction of eligible inputs without acknowledgement by the declared deadline. |
| Emotional experience | `target_emotion_rate` | Fraction of consented participants reporting the predefined emotion at the intended moment. |
| Emotional experience | `unintended_distress_rate` | Fraction reporting unintended distress under the predefined severity and collection procedure. |

Set thresholds per audience and device before collecting data. The evaluator distinguishes missing, insufficient and synthetic-only measurements from thresholds met by compatible evidence. It checks declared criteria and provenance. A reference should identify a source that the reviewer can inspect.
