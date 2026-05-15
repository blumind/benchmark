# BluMind Benchmark — Scripts

Validators and pipeline tools.

## Setup

Python 3.10+ required.

The benchmark scripts use non-trivial dependencies (`litellm`, `jsonschema`,
`python-dotenv`, `PyYAML`). To keep them isolated from your system Python and
to make the environment reproducible, **always work inside a virtual
environment**.

### One-time setup (after cloning the repo)

From the repository root:

```bash
# 1) Create the venv (only the first time)
python3 -m venv .venv

# 2) Activate it
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate              # Windows PowerShell

# 3) Install dependencies inside the venv
pip install -r scripts/requirements.txt
```

`.venv/` is excluded by `.gitignore`; it never gets committed. Each
collaborator creates their own.

### Every time you open a new terminal

Re-activate the venv before running anything:

```bash
cd /path/to/blumind-benchmark
source .venv/bin/activate
```

You will know you are inside the venv because your shell prompt is
prefixed with `(.venv)`. If a command fails with
`ModuleNotFoundError: No module named 'litellm'` (or similar), you forgot
to activate.

To leave the venv: `deactivate` or simply close the terminal.

### Optional shell alias

Add to `~/.zshrc` or `~/.bashrc` to enter the project with a single
command:

```bash
alias blumind='cd /path/to/blumind-benchmark && source .venv/bin/activate'
```

## Validators

Each validator checks one type of artifact against its JSON Schema and runs
cross-file invariants. Run from the repo root (or any subfolder — the
validators auto-locate the repo root by looking for `system/schemas/v1.0/`).

```bash
python scripts/validate_response.py            # all .json under responses/
python scripts/validate_gold.py                # all *_gold.md under golds/
python scripts/validate_evaluation.py          # all .json under scoring/
python scripts/validate_registry.py            # subjects/registry.yaml

python scripts/validate_response.py path/to/file_or_dir   # narrow scope
```

Each validator prints `PASS` / `FAIL` per file with detailed errors and exits
with code `0` (all valid) or `1` (any failure). Suitable for direct use in CI.

## Files

| File | Validates against | Default target |
|---|---|---|
| `validate_response.py` | `system/schemas/v1.0/response.schema.json` | `responses/` |
| `validate_gold.py` | `system/schemas/v1.0/gold.schema.json` | `golds/` |
| `validate_evaluation.py` | `system/schemas/v1.0/evaluation.schema.json` | `scoring/` |
| `validate_registry.py` | `system/schemas/v1.0/registry.schema.json` | `subjects/registry.yaml` |
| `_validator_common.py` | (shared utilities; not run directly) | — |

## Pipeline tools

### `run_evaluation.py` — generate model responses

Calls the LLM API of one or more subjects, captures the raw response, wraps
it with the six traceability fields, validates against
`response.schema.json`, and stores the result. Powered by [LiteLLM][litellm]
under the hood, so any of its 100+ supported providers works without code
changes — just register the subject in `subjects/registry.yaml`. Design
rationale: `docs/run_evaluation_design.md`.

[litellm]: https://github.com/BerriAI/litellm

#### One-time setup

1. Install dependencies (now includes `litellm` and `python-dotenv`):

   ```bash
   pip install -r scripts/requirements.txt
   ```

2. Copy the env template and fill in your keys:

   ```bash
   cp .env.example .env
   # edit .env, paste OPENAI_API_KEY and ANTHROPIC_API_KEY
   ```

   The `.env` file is gitignored. The `.env.example` is committed so
   collaborators know which keys are required.

#### Common invocations

```bash
# Single case, single subject (recommended for the first smoke test)
python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5

# All FOUL cases, single subject
python scripts/run_evaluation.py --family FOUL --subject gpt-5

# All cases, single subject
python scripts/run_evaluation.py --subject gpt-5

# Full battery: every case × every kind=llm subject in the registry
python scripts/run_evaluation.py --all

# Pin a non-latest subject_version
python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5 \
    --subject-version gpt-5-2026-03-15

# Override the LiteLLM model identifier (e.g. for a staging endpoint)
python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5 \
    --litellm-model openai/gpt-5-2026-03-15

# Print the plan without spending API budget
python scripts/run_evaluation.py --all --dry-run
```

If no filters are passed, the script refuses to run unless `--all` is
explicit, to prevent accidental full batteries.

#### Outputs

| Outcome | Location |
|---|---|
| Validated response | `responses/v1.0/<subject_id>/<case_id>__<run_id>.json` |
| Failed run (raw text + diagnostic) | `responses/v1.0/<subject_id>/_errors/<case_id>__<run_id>.{txt,error.log}` |
| Per-call telemetry (tokens + cost + latency) | `logs/batch_logs/<UTC-timestamp>.csv` (gitignored) |

The `run_id` is auto-incremented per `(subject_id, case_id, UTC date)`:
`run-YYYY-MM-DD-NNN`. Re-running an existing case generates a new `run_id`;
previous runs are never overwritten (responses are append-only by design).

#### Behaviour

- **Retries**: 3 attempts with exponential backoff per call, delegated to
  LiteLLM's `num_retries`. Configurable with `--retries N`.
- **Schema validation**: every response is validated against
  `response.schema.json` before being saved as success. A failing run is
  classified as an error and never lands in the success path.
- **Error isolation**: a single failing run never aborts the batch; the
  script proceeds to the next `(case, subject)` pair.
- **Cost & token telemetry**: every successful call is annotated with
  `prompt_tokens`, `completion_tokens`, USD cost (via
  `litellm.completion_cost`) and latency. Per-call values are printed
  inline next to PASS/FAIL, and the batch summary at the end shows totals
  plus a per-subject cost breakdown. The full per-call CSV lives under
  `logs/batch_logs/` and is gitignored — it is operational telemetry, not
  benchmark output. Provider dashboards (OpenAI, Anthropic, …) remain the
  authoritative source for billing; cost figures here may lag dashboard
  pricing by hours when a provider changes rates. See
  `docs/run_evaluation_design.md` § 6 for the full design rationale.

### `compute_metrics.py` — derive aggregated metrics

Reads every scored response under `responses/`, `scoring/` and `golds/` for a
benchmark version, applies the rubric (per-case classification + safety
gate) and the aggregated formulas (`Pass rate`, `mean clipped score`, soft
Brier, soft 10-bin ECE, `Q_final` composite). Writes three deterministic
CSVs under `results/`. Formulas and justifications:
[`system/rubric/v1.0/aggregated_metrics.md`](../system/rubric/v1.0/aggregated_metrics.md).

```bash
python scripts/compute_metrics.py                    # default: v1.0, alpha=0.5
python scripts/compute_metrics.py --alpha 0.7         # weight Pass rate higher in Q_final
python scripts/compute_metrics.py --strict           # treat unscored responses as errors
python scripts/compute_metrics.py --quiet            # suppress per-row progress
```

#### Outputs

| File | Granularity |
|---|---|
| `results/per_run.csv` | One row per (case, subject, run, reviewer) — every derived value |
| `results/metrics_per_subject.csv` | One row per subject — `pass_rate`, `mean_clipped_score`, `brier`, `ece`, `q_final`, `leaderboard_status` |
| `results/metrics_per_family.csv` | One row per (subject, family) — pass rate and mean score by family |

#### Behaviour

- **No re-validation**: assumes the dedicated validators have already passed
  on inputs; consumes them directly.
- **Cross-file invariants**: aborts (exit 1) on duplicate scoring per
  triplet, scoring without matching response, or scoring without matching
  gold.
- **Empty inputs**: writes CSVs with headers only and exits 0; useful as a
  smoke test before any scoring exists.
- **Determinism**: rows are sorted by stable keys; two runs over the same
  input produce byte-identical CSVs.

### `compute_operational.py` — derive operational metrics

Aggregates the per-call telemetry written by `run_evaluation.py` into
two operational tables that sit alongside the quality leaderboard. The
two views answer different questions and must not be conflated:

| Table | Question |
|---|---|
| `metrics_per_subject.csv` | Is the subject **good at diagnosing**? |
| `operational_per_subject.csv` | Is the subject **practical to use**? |

The shared key is `subject_id`. A reader who wants a single combined
view joins them externally.

```bash
python scripts/compute_operational.py
python scripts/compute_operational.py --quiet
```

#### Inputs

Every CSV under `logs/batch_logs/` (gitignored, append-only). Only rows
with `status == "pass"` are aggregated; failed runs are not part of the
operational baseline because their tokens come from invalid responses.

#### Outputs

| File | Granularity |
|---|---|
| `results/operational_per_subject.csv` | One row per `(subject_id, subject_version)` |
| `results/operational_per_family.csv` | One row per `(subject_id, subject_version, family)` |

Both share these columns: `n_runs`, `mean_input_tokens`,
`mean_output_tokens`, `output_to_input_ratio` (verbosity index),
`median_latency_s`, `p95_latency_s`, `price_per_input_token_usd`,
`price_per_output_token_usd`. The per-family view adds the `family`
column as part of the key.

#### Statistical conventions

- **Tokens**: mean. Bounded distribution, mean is well-behaved.
- **Latency**: median + p95. Long-tail distribution; the mean is
  vulnerable to one slow timeout. p95 is computed by linear
  interpolation, robust at small `n`.
- **Unit pricing**: mean across the runs in the bucket. Within a single
  benchmark version pricing should be constant; the average is
  defensive against rare provider-side price updates mid-batch.

#### What this script intentionally does NOT publish

- Absolute USD spend per subject. The unit prices are exposed instead;
  any reader can multiply them by tokens to compute their own total
  cost. Publishing your invoice is operational noise that does not
  belong in the benchmark.

### Other pipeline tools (planned)

- `aggregate_scoring.py` — consolidate per-reviewer scoring into per-response rows (v2.0).
- `build_leaderboard.py` — emit `results/leaderboard.csv` and HTML from `metrics_per_subject.csv`.
- `emit_seal.py` — (v2.0+) sign and issue digital certificates.
