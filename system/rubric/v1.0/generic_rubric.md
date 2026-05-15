# Generic evaluation rubric — BluMind Benchmark v1.0

This rubric applies to every response (from a human expert or an LLM) against any case in v1.0, regardless of family. Cases are identified as `RO-<FAMILY>-<NNN>` where `<FAMILY>` is one of `OXID`, `SCAL`, `FOUL`, `MECH`, `NOWE` (see `system/families/v1.0/taxonomy.md`). Each criterion is scored 0-2, with a maximum total of 12 points.

The schema field `confidence` is **not scored in this rubric**; it is treated as a longitudinal calibration metric of the evaluated subject (see final section). The fields `case_id`, `benchmark_version`, `subject_id`, `subject_version`, `run_id` and `timestamp_utc` are traceability metadata and are not scored either.

---

## Bilingual glossary for reviewers

Since public artifacts are in English but case statements and golds are authored in Spanish (see `README.md`, Language policy), this glossary fixes shared vocabulary:

| English | Spanish | Notes |
|---|---|---|
| Oxidative damage | Daño oxidativo | Family `OXID` |
| Inorganic scaling | Scaling inorgánico | Family `SCAL` |
| Organic / biological fouling | Fouling orgánico / biológico | Family `FOUL` |
| Mechanical damage / integrity | Daño mecánico / integridad | Family `MECH` |
| No-wetting / abnormal startup | No-wetting / arranque anómalo | Family `NOWE` |
| Root cause | Causa raíz | — |
| Rejection drop | Caída de rechazo | — |
| Salt passage | Paso de sales | — |
| Permeate | Permeado | — |
| Feed | Alimentación | — |
| Reject / concentrate | Rechazo / concentrado | — |
| Differential pressure (ΔP) | Presión diferencial | — |
| Recovery | Recovery / rendimiento | Usually kept as "recovery" in Spanish too |
| CIP (Clean-In-Place) | Limpieza química | — |
| Decay test | Prueba de integridad por decay | — |
| Per-tube permeate profile | Perfil de permeado por tubo | — |

---

## Case types — Quick classification rule

Before scoring, the reviewer classifies the case into one of four **types**. The type is declared in the gold and carries implications for how the rubric is applied.

| Type | Rule | Typical use |
|---|---|---|
| **Closed** | One correct hypothesis, sufficient data in the statement to reach it. | Benchmark floor — any reasonable model should pass. |
| **Semi-closed** | One most likely hypothesis, but some data is missing. Asking for the right additional datum is expected but not mandatory for a Pass. | Most common in v1.0. |
| **Open** | Multiple technically valid hypotheses. The rubric scores the *reasoning quality*, not a single "right" answer. | Discrimination via alternatives and counterfactual thinking. |
| **Ambiguous** | Not enough data to commit to a single hypothesis. Asking for data **is mandatory** for a Pass. Committing to a single hypothesis without asking is an automatic fail (recoverable). | Edge cases, `NOWE` style situations. |

### Implications per criterion by case type

| Criterion | Closed | Semi-closed | Open | Ambiguous |
|---|---|---|---|---|
| Main hypothesis | Must match gold. | Must match gold's dominant one. | Any gold-accepted hypothesis scores. | No single answer required; score the framing. |
| Alternatives | Expected but not required for 2 pts. | Expected with substantive justification; an alternative judged 0 under the scoring criteria caps this criterion at 1. | **Decisive** — must discriminate well. | Must enumerate the live candidates. |
| Requested data | Optional; may score if it confirms the closed answer. | Expected. | Useful but secondary. | **Mandatory**. No ask → recoverable automatic fail. |
| Recommended action | Must be the canonical action. | Must be safe; may be conditional. | Conditional actions are expected. | "Hold and gather" actions score highest. |
| Decision-change condition | Useful. | Important. | **Decisive**. | **Decisive**. |

---

## Scoring criteria

| Criterion | 0 points | 1 point | 2 points |
|---|---|---|---|
| **Main hypothesis** | Incorrect or irrelevant | Identifies a symptom but not the likely root cause | Identifies the exact root cause (e.g. oxidation, no-wetting, silica scaling, etc.) |
| **Key signals** | Does not mention case data | Mentions isolated signals without connecting them | Explains the relationship between variables (e.g. NPF↑ + rejection↓ simultaneously = chemical damage, not fouling) |
| **Alternatives** | Alternatives are formally present but semantically empty: (a) duplicate or paraphrase of the main hypothesis, (b) belong to a family already excluded by a signal explicit in the case, or (c) `why_plausible` / `why_discardable` are non-informative boilerplate ("it is possible", "less likely", "cannot be ruled out") with no technical content | Proposes at least one alternative from a different family with minimally substantive justification, but the discrimination is weak or partially contradicts case signals | Proposes at least one technically solid, differentiated alternative with a `why_discardable` that references a **specific signal from the case** (e.g. "o-ring leak discarded because salt passage profile is stage-uniform, not tube-localized") |
| **Safe action** | Action that damages the membrane (e.g. acid on oily organic fouling) | Generic action (e.g. "clean") | Specific and safe action, compatible with manuals (e.g. alkaline CIP with SDS; preventive shutdown; vessel profiling) |
| **Next datum** | No data requested or irrelevant data requested | Requests standard manual data | Requests the "trigger" datum that truly discriminates (e.g. zeta potential, manual ORP with DPD, BGP, integrity by decay test) |
| **Criterion robustness** | Does not define under what condition the decision would change | Generic or trivial condition ("if it gets worse", "if it does not improve") | Specific, discriminating condition that shows counterfactual reasoning (e.g. "if ORP drops below 250 mV or salt passage rises >0.3 points in 12 h, switch to oxidative-damage hypothesis") |

**Total:** 0-12 points.

---

## Automatic fails (disqualify the case regardless of score)

These are actions or recommendations that, even if the response scores highly on other criteria, mark the case as **fail due to risk**.

### Generic automatic fails

1. **Raising feed pressure to compensate for a flow drop without prior diagnosis.** Classic junior-operator error; an expert never recommends it without first isolating the cause.
2. **Recommending acid CIP when oxidative damage or lipidic organic fouling is suspected.** Can accelerate irreversible deterioration.
3. **Recommending CIP without first verifying mechanical integrity (o-rings, seals) when there is a simultaneous change in salt passage and flow.**
4. **Not requesting any additional datum in an ambiguous case.** In `Ambiguous`-type cases, closing with a single hypothesis without asking for confirmation is disqualifying.
5. **Ignoring signals that contradict the main hypothesis.** If salt passage contradicts the diagnosis (e.g. scaling diagnosis with salt passage dropping), ignoring it is a fail. The `gold` declares these as `non_ignorable_signals`: silently ignoring any of them triggers this fail.

### Case-specific automatic fails

Each gold file (`golds/RO-<FAMILY>-<NNN>_gold.md`) adds **0-3 case-specific automatic fails**. Example for `RO-OXID-003` (free chlorine suspicion):

- Recommending "monitor without stopping" in the face of a free chlorine suspicion → automatic fail (every additional minute is irreversible damage).
- Recommending CIP before an integrity test → automatic fail (confuses chemical damage with fouling).

---

## Fail severity: critical vs recoverable

Each automatic fail — generic or case-specific — carries a **severity label** that determines the final classification:

- **Critical** → the response is marked as **Fail**, regardless of the 0-12 score.
- **Recoverable** → the response is marked as **Conditional**, regardless of the 0-12 score.

### Criteria for assigning severity

An automatic fail is **critical** if it fails either of these two tests:

1. **Irreversibility test.** If the recommendation is executed, no subsequent action can save the membrane (chemical damage on polyamide, overpressure on a compromised element, active oxidant without feed cut-off).
2. **Time-window test.** There is no time between the recommendation and the damage for a second review layer to catch it (minute-by-minute damage).

If both tests are passed (the damage is reversible AND there is an operational rescue window), the fail is **recoverable**.

### Default severity of generic automatic fails

| # | Generic automatic fail | Default severity | Justification |
|---|---|---|---|
| 1 | Raising feed pressure without diagnosis | **Critical** | If the real cause is scaling, oxidation or mechanical damage, overpressure accelerates irreversible deterioration of the element. |
| 2 | Acid CIP under suspicion of oxidative damage or lipidic fouling | **Critical** | The acid fixes oils against the membrane or accelerates hydrolysis of already-oxidized polyamide. No way back. |
| 3 | CIP without prior mechanical integrity check | **Recoverable** | Error of order, not of destination. A senior operator can stop before injecting chemicals and run a decay test first. |
| 4 | No additional data requested in ambiguous case | **Recoverable** | Method error, not action error. If there is cross-review before execution, it can be caught in time. |
| 5 | Ignoring signals that contradict the hypothesis | **Recoverable** | Judgment error. Can escalate to critical if the ignored signals point to an irreversible process (see override rule). |

### Severity of case-specific automatic fails

Each gold file (`golds/RO-<FAMILY>-<NNN>_gold.md`) explicitly declares the severity of its 0-3 case-specific automatic fails. Example for `RO-OXID-003` (free chlorine suspicion):

| Case-specific fail (RO-OXID-003) | Severity | Justification |
|---|---|---|
| Recommending "monitor without stopping" against free chlorine | **Critical** | Continuous exposure to oxidant; polyamide damage is minute-by-minute and irreversible. |
| Recommending CIP before an integrity test | **Critical** | Confuses chemical damage with fouling; the applied chemical destroys already-compromised elements. |

### Override rule

The `gold` of a case may **escalate** the severity of a generic automatic fail if the operational context justifies it. Example: "ignoring contradictory signals" is recoverable by default, but in a case with active-oxidant suspicion, the gold may declare it critical because the time window disappears.

The `gold` can never **downgrade** a generic critical automatic fail to recoverable. Severity only goes up, never down. This keeps the rubric monotonic: additional information can worsen the classification, never improve it.

### Resolution rule when several automatic fails coincide

If a response incurs several automatic fails simultaneously, the most serious wins: any critical → **Fail**. Only recoverable → **Conditional**. The committee may politically decide that the accumulation of ≥3 recoverable fails degrades to Fail, but that is committee policy, not rubric policy.

---

## Classification thresholds

Total scale 0-12.

| Score | Automatic fail | Classification |
|---|---|---|
| ≥ 10 | No | **Pass** |
| 7-9 | No | **Conditional** |
| < 7 | No | **Fail** |
| Any | Yes (recoverable) | **Conditional** |
| Any | Yes (critical) | **Fail** |

### Case-specific floor and ceiling (gold override)

The `gold` of a case may modulate these generic thresholds via two fields (see `system/schemas/v1.0/gold.schema.json`):

- **`rubric_ceiling`** (1-12, default 12). The raw 0-12 score is **clipped** to this value before the thresholds above are applied. Used for Ambiguous or Open cases where the available evidence does not support a perfect diagnosis (e.g. `rubric_ceiling: 10` → a raw score of 12 becomes 10, still Pass).
- **`rubric_floor`** (0-11, default 0). A raw score strictly below this value is classified **Fail** regardless of the generic thresholds. Used for high-stakes cases where `Conditional` is not an acceptable outcome (e.g. active free-chlorine suspicion with `rubric_floor: 10` → any raw score < 10 is Fail).

Order of application (deterministic):

1. Compute the raw 0-12 score from the six criteria.
2. Clip to `rubric_ceiling`.
3. If the clipped score is strictly below `rubric_floor` → **Fail**.
4. Otherwise apply the generic Pass/Conditional/Fail thresholds to the clipped score.
5. Automatic fails (generic or case-specific) override the result per the table above.

The floor/ceiling mechanism is monotonic with the rest of the rubric: it can only make the classification stricter, never more lenient.

---

## Longitudinal calibration of the evaluated subject (separate metric)

The schema field `confidence` (0-100) is **not scored per case**. It is stored alongside the real result and evaluated in aggregate per evaluated subject, across 30+ cases:

- `reported_confidence`: value declared by the subject in the response (schema field `confidence`).
- `correctness`: 1 if the main hypothesis is correct per the `gold`, 0.5 if partially correct, 0 if incorrect.

With enough cases, calibration metrics (Brier score, Expected Calibration Error) are computed per evaluated subject. The operational interpretation is:

- **Well-calibrated**: the declared average confidence matches the actual hit rate.
- **Overconfident**: declares high confidence and is right less often than claimed.
- **Underconfident**: declares low confidence but is right more often than claimed.

Calibration does not affect the Pass/Conditional/Fail classification of the individual case, but it does weight the subject's role in training datasets: overconfident subjects are filtered or discounted, well-calibrated ones are prioritized.

The exact formulas (Brier with soft `correctness`, ECE with 10 fixed-width bins), the subject-level composite `Q_final` and the safety gate that disqualifies subjects with critical fails are documented in [`system/rubric/v1.0/aggregated_metrics.md`](aggregated_metrics.md).

---

## Application notes

- The rubric is applied by a human expert (reviewer) on the JSON response of the evaluated subject.
- For partial automation: some criteria can be scored by comparison against `golds/RO-<FAMILY>-<NNN>_gold.md` using regex or embeddings. The final score is validated by a human.
- Store one row per (case, evaluated subject, version, score per criterion, total score, reported confidence, correctness, automatic fails, classification) under `results/` (see pipeline in `scripts/aggregate_scoring.py` and `scripts/compute_metrics.py`). The source-of-truth per-scoring JSON files live under `scoring/v1.0/<subject_id>/`.
- If two reviewers score differently, the discrepancy is preserved as valuable data (no forced consensus in ambiguous cases).

---

## Design rule

Every field requested from the evaluated subject in the schema must have a declared evaluation purpose: **per-case rubric**, **longitudinal metric**, or **operational metadata**. No field without a declared purpose.

Current schema status (field names per `system/schemas/v1.0/response.schema.json`):

| Schema field | Purpose |
|---|---|
| `case_id` | Operational metadata (traceability) |
| `benchmark_version` | Operational metadata (traceability) |
| `subject_id` | Operational metadata (traceability) |
| `subject_version` | Operational metadata (traceability) |
| `run_id` | Operational metadata (traceability) |
| `timestamp_utc` | Operational metadata (traceability) |
| `main_hypothesis` | Rubric — criterion 1 (Main hypothesis) |
| `confidence` | Longitudinal metric — calibration |
| `key_signals` | Rubric — criterion 2 (Key signals) |
| `alternatives` | Rubric — criterion 3 (Alternatives) |
| `recommended_action` | Rubric — criterion 4 (Safe action) |
| `requested_data` | Rubric — criterion 5 (Next datum) |
| `decision_change_condition` | Rubric — criterion 6 (Criterion robustness) |
