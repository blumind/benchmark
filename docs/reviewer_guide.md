# Reviewer guide — BluMind Benchmark v1.0

This guide is for the human reviewer who scores LLM responses against the
benchmark's gold standards. It is the operational complement to the
rubric: the rubric tells you **what** to score; this guide tells you
**how** to operate during a scoring session so that the result is
consistent, auditable and free from common biases.

If you have not yet read the rubric, do that first:
[`system/rubric/v1.0/generic_rubric.md`](../system/rubric/v1.0/generic_rubric.md).

---

## 1. Pre-flight checklist

Before opening the first case, have on hand:

- The rubric (`system/rubric/v1.0/generic_rubric.md`).
- Your assigned reviewer ID (e.g. `R01`). It will be embedded in every
  output file.
- The current benchmark version (`v1.0`).
- Access to:
  - `cases/v1.0/` — case statements (public).
  - `golds/v1.0/` — gold standards (private; never share or commit).
  - `responses/v1.0/<subject>/` — model responses to score.
  - `system/schemas/v1.0/evaluation.schema.json` — the contract for
    your output, in case you produce it manually.

If any of the above is missing, stop and obtain it before scoring.
Scoring without the gold or without the rubric is not valid scoring.

---

## 2. Reading order per case

Always in this order, never skipping or reordering:

1. **Case statement** (`cases/v1.0/RO-XXX-NNN.md`). Establishes the
   operational context of the case as the model received it.
2. **Gold** (`golds/v1.0/RO-XXX-NNN_gold.md`). Defines the canonical
   answer, the non-ignorable signals, the case-specific automatic
   fails, and any `rubric_floor` / `rubric_ceiling` overrides.
3. **Response** (`responses/v1.0/<subject>/RO-XXX-NNN__run-...json`).
   The object to be scored.

**Why this order matters.** Reading the response first contaminates
your reading of the gold (you unconsciously look for confirmation of
what the model said). Reading the gold before the response keeps you
anchored to the technical truth of the case, not to the model's framing.

---

## 3. Scoring discipline

### 3.1 Anchors come from the rubric, not from intuition

For each of the six criteria, find the **specific behaviour** the
rubric requires for a `2` (numerical threshold, named discriminating
datum, alternative referenced to a case signal, etc.). If you cannot
point to that behaviour literally in the response, the score is not 2,
even if the response "feels good".

Likewise, `0` is not "very bad". `0` is **criterion absent or
semantically empty** (boilerplate, paraphrase of another field, ignored
non-ignorable signal). Frontier models do reach `0` on specific
criteria — most often on `Alternatives` and `Decision-change condition`.

### 3.2 Justification is mandatory for every score

Including `2`. The justification is one technical sentence that names
the rubric anchor you applied (or did not find). It is what enables:

- Audit by the committee.
- Calibration comparison between reviewers.
- Detection of gold-anchoring (penalising vocabulary differences
  rather than technical content).

A justification that says only "complete" or "incomplete" is
insufficient. State the anchor.

### 3.3 Tie-breaking: when in doubt, go down

If you hesitate between `1` and `2`, the score is `1`. If you hesitate
between `0` and `1`, the score is `0`. The rubric is a strict
threshold model: `2` is awarded for **observed evidence** of the
anchor, not for **plausible inference**. The same rule applies in
reverse for downgrades — you do not invent reasons to award.

### 3.4 When the rubric does not cover something

It will happen. A response will do something the rubric did not
anticipate. In that case:

- Do **not** invent a new criterion or a new anchor.
- Score the existing six criteria as best you can with the existing
  anchors.
- Capture the gap in `reviewer_notes`. The committee uses these notes
  to refine the rubric in future versions.

The rubric evolves through documented gaps, not through reviewer
improvisation.

### 3.5 Automatic fails

Check the response against:

1. The five **generic automatic fails** (rubric, section
   "Generic automatic fails").
2. The **case-specific automatic fails** declared in the gold's
   `case_specific_automatic_fails` array.

For each triggered fail, record:

- `type`: `"generic"` or `"case_specific"`.
- `reference`: the generic fail number (1-5) or the exact gold
  description.
- `severity`: the effective severity after the gold's possible
  escalation (golds may escalate, never downgrade).
- `justification`: one sentence pointing to the specific text in the
  response that triggered the fail.

### 3.6 `correctness` for calibration

`correctness ∈ {0, 0.5, 1}` is independent from the criterion scores
and from the automatic fails. It records only whether the **main
hypothesis** matches the gold, regardless of how the model articulated
it. It feeds the longitudinal calibration metrics (Brier, ECE) — not
the per-case Pass/Conditional/Fail classification.

- `1` — main hypothesis is one of the `accepted_main_hypotheses`.
- `0.5` — main hypothesis is in the right family but mis-specifies the
  mechanism (e.g. "fouling" when the gold expects "biofouling
  organic").
- `0` — main hypothesis is wrong or absent.

---

## 4. Output: where the JSON goes

For each scored response, produce one JSON file at:

```
scoring/v1.0/<subject_id>/<case_id>__<run_id>__eval-<reviewer_id>.json
```

The JSON conforms to
[`system/schemas/v1.0/evaluation.schema.json`](../system/schemas/v1.0/evaluation.schema.json).
After saving any new files, run:

```
python scripts/validate_evaluation.py
```

A non-zero exit means at least one file violates the schema. Fix the
flagged file before continuing.

---

## 5. Pacing and calibration

### 5.1 Recommended pace

- **5-7 minutes per case** in steady state. Faster usually means you
  are not reading the gold; slower usually means you are debating
  yourself between `1` and `2` (apply 3.3).
- **No more than 10-12 cases per uninterrupted block.** Calibration
  drifts; senior reviewers report visible differences in scoring
  strictness across long sessions.
- Take a 10-minute break between blocks.

### 5.2 Self-calibration check

After the first 5 cases of a session, re-open case 1, re-read the
response and your justifications. If you would now score it
differently:

- The earlier score was correct → leave it; you have over-corrected.
- The earlier score was wrong → fix it now and continue.

If three of the first five would change, stop. Re-read the rubric and
restart the session. Your calibration drifted before stabilising.

### 5.3 Single-response evaluation

When scoring a response from one subject (e.g. GPT-5) on a given case,
**do not look at the response from another subject** (e.g. Claude) on
the same case. Each response is judged in isolation against the gold,
not comparatively. Comparative reading inflates the better response
and depresses the worse one.

---

## 6. Disagreement between reviewers

When two reviewers score the same `(case, subject, run)`:

- Both files coexist in `scoring/v1.0/<subject_id>/`. Do **not**
  overwrite.
- Forced consensus is not pursued. Disagreement is preserved as
  signal: it indicates a case where the rubric is ambiguous, the gold
  is under-specified, or both reviewers genuinely interpret the
  evidence differently.
- The committee aggregates disagreements per family in v2.0 to refine
  the rubric and the gold catalogue.

---

## 7. Privacy

Golds are private intellectual property. As a reviewer, you may:

- Read them locally.
- Quote them in `reviewer_notes` to justify a score, since notes stay
  private to the committee until the gold is published.

You may **not**:

- Share gold files with anyone outside the reviewer roster.
- Commit `golds/v1.0/` to any public location.
- Paste gold content into third-party services (LLM playgrounds, AI
  assistants, search engines, public chats).

If you are unsure whether a destination is acceptable, ask before
sharing.

---

## 8. What to do when stuck

- The case statement is missing a piece of context you would normally
  expect → the case is intentionally `Ambiguous` or `Open`. Score on
  the framing and the question for additional data, per the rubric's
  case-type table.
- The model produced something that violates the response schema (you
  will rarely see this; the runner validates) → flag it in
  `reviewer_notes` and score what is intelligible. If the response is
  unintelligible, score the missing criteria as `0` and add a note.
- You have a fundamental disagreement with the gold → score the
  response according to the rubric and the gold as written, and add a
  note. Do not score against your preferred answer; the committee
  reviews gold contestation separately.

---

## 9. Closing checklist for a scoring session

Before finishing a session:

- [ ] All scored cases have JSON files under `scoring/v1.0/`.
- [ ] `python scripts/validate_evaluation.py` exits with `0`.
- [ ] No gold files have been moved, copied, shared or pasted
      anywhere outside this repository.
- [ ] `reviewer_notes` is non-empty for any case that surprised you,
      that the rubric did not cover, or where you suspect the gold
      may need refinement.

When all four are checked, the session is closed and the data is ready
for `compute_metrics.py`.

---

## 10. Premium contributions for the commercial datasets

The benchmark is published openly, but BluMind also produces **commercial
training datasets** sold to AI labs interested in fine-tuning models on
RO-engineering reasoning. Two premium contributions feed those datasets:

> **Privacy contract.** Both contributions described below are
> **intentionally omitted** from the public benchmark export by
> `scripts/export_public.py`. Only the schemas are public — the contents
> live in private storage and are released only to commercial buyers.
> Reviewers must NOT publish or share these contents outside the repo.

### 10.1 `justification_long` — for the evaluator dataset (`explanations.jsonl`)

**Role**: Reviewer / Scorer (same as everything above).
**Where**: per-criterion field inside `scoring/v1.0/<subject>/<case>__*__eval-R01.json`.
**When**: optional; recommended for the **top-3 and bottom-3** responses per case
(the highest-signal examples for teaching an auto-judge).

While the regular `justification` is **telegraphic** (one short line that
audits the score: *"Anchor 'biofouling 1ª etapa' matched."*), the
`justification_long` is **rich expert prose** (3-6 sentences) that explains:

1. What the model got right and which mechanism it correctly identifies.
2. What an expert would have added, corrected or emphasized.
3. The technical context — thresholds, ratios, non-obvious anchors — needed
   for a downstream auto-judge to learn the reasoning behind the score.

Example for `main_hypothesis` on a top response:

> *"The model correctly identifies localized bioincrustation at the head
> elements of stage 1 as the dominant hypothesis. The causal chain
> (DAF operating at 60% efficiency → organic carryover → preferential
> deposition on the first membrane of each vessel) is mechanistically
> sound, and explains why ΔP increases in stage 1 while stage 2 remains
> stable. An experienced expert would additionally have emphasized that
> the ΔP1/ΔP2 ratio is the cleanest discriminant between localized and
> generalized fouling — the model mentions it but does not anchor it. The
> answer is complete; what is missing is the operational threshold
> (ΔP1/ΔP2 > 2.5 typically indicates localized fouling)."*

Leave `justification_long` absent for evaluations that should not be
exported (e.g. middle-of-the-pack responses, mostly redundant signal).

### 10.2 `ideal_responses/v1.0/<case_id>_ideal.json` — for the responder dataset (`sft.jsonl`)

**Role**: Ideal-response Author (cognitively different from scoring; see
the schema for required metadata).
**Where**: a new file per case under `ideal_responses/v1.0/`.
**When**: one file per case; only `status: approved` files are exported.

The gold file (`golds/v1.0/<case>_gold.md`) is an **evaluative framework**
listing accepted hypotheses, signals and actions — it tolerates multiple
valid answers. An `ideal_response` is **one concrete answer** that
satisfies that framework, written by a senior expert and suitable as a
training target.

Two strategies are recognized (see `source_strategy` in the schema):

- **Expert-curated from LLM** (5-8 h for 31 cases): take the top-scored
  LLM response, refine it manually; cheapest path. Record the seed
  reference in `seed_response_ref`.
- **Expert-authored from scratch** (15-25 h): write the answer end-to-end;
  highest commercial value, especially in the **expert-pair** variants
  where a second expert reviews.

Schema and validator: `system/schemas/v1.0/ideal_response.schema.json`
and `scripts/validate_ideal_response.py`.

Optional but recommended for premium tier: fill the
`expert_chain_of_thought` field — a 5-15-sentence first-person narrative
of *how* the answer was reached (what was looked at first, what was
discarded, what thresholds applied). This is the most valuable training
signal for teaching a model to reason like a senior RO engineer.

### 10.3 Quick reference

| Premium contribution             | Role                | Lives in                                            | Feeds                |
|----------------------------------|---------------------|-----------------------------------------------------|----------------------|
| `justification_long` (per crit.) | Reviewer / Scorer   | `scoring/v1.0/<subject>/<case>__*__eval-R01.json`   | `explanations.jsonl` |
| `<case_id>_ideal.json`           | Ideal-resp. Author  | `ideal_responses/v1.0/`                             | `sft.jsonl`          |

Both are **optional for benchmark validity**, **required for commercial
export of that entry**. Leaving them empty is fine; they are filled
progressively as the dataset is enriched.

