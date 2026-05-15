"""Per-call cost and token telemetry helpers for `run_evaluation.py`.

Captures usage and pricing data emitted by LiteLLM, prints inline tails
next to PASS/FAIL lines, summarises a batch when the run loop finishes
and persists every call to a gitignored CSV under `logs/batch_logs/`.

Design rationale: see `docs/run_evaluation_design.md` § 6 (per-call cost
and token telemetry). This module keeps the runner orchestrator narrow
and lets the same helpers be reused by future scripts that share the
same cost-tracking conventions (e.g. `run_human_intake.py`).

Defensive policy: every numeric field is independently optional. If the
provider does not return ``usage`` or LiteLLM has no pricing entry for
the model, the corresponding cells are left empty and the runner keeps
working — telemetry must never abort an evaluation batch.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _validator_common import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
)


BATCH_LOG_FIELDS = [
    "timestamp_utc", "case_id", "subject_id", "subject_version", "run_id",
    "track",
    "litellm_model", "served_model",
    "prompt_tokens", "completion_tokens", "total_tokens",
    "cost_usd", "price_per_input_token_usd", "price_per_output_token_usd",
    "latency_ms", "status", "error_type",
]


def extract_call_metrics(
    response: Any, latency_ms: int, litellm_module: Any, litellm_model: str
) -> dict[str, Any]:
    """Pull token counts, USD cost and unit pricing from a LiteLLM response.

    Defensive against provider variations: every numeric field defaults
    to ``None`` if the underlying attribute is missing or LiteLLM cannot
    price the model. Never raises; the calling pipeline must keep
    working even when telemetry is partial.

    Unit pricing is read from LiteLLM's ``model_cost`` lookup table at
    the time of the call, so the value persisted in the batch log
    reflects the price at run time (not at aggregation time). This makes
    operational metrics auditable even if the provider changes its
    rates after the benchmark version is published.
    """
    def _get(obj: Any, key: str) -> Any:
        if obj is None:
            return None
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict):
            return obj.get(key)
        return None

    usage = _get(response, "usage")
    prompt_tokens = _get(usage, "prompt_tokens")
    completion_tokens = _get(usage, "completion_tokens")
    total_tokens = _get(usage, "total_tokens")

    try:
        cost_usd = litellm_module.completion_cost(completion_response=response)
        cost_usd = float(cost_usd) if cost_usd is not None else None
    except Exception:
        cost_usd = None

    price_in, price_out = _lookup_unit_prices(litellm_module, litellm_model)

    served_model = _get(response, "model")
    if isinstance(served_model, str) and served_model:
        served_model = served_model.split("/", 1)[-1]
    else:
        served_model = None

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "price_per_input_token_usd": price_in,
        "price_per_output_token_usd": price_out,
        "latency_ms": latency_ms,
        "served_model": served_model,
    }


def _lookup_unit_prices(litellm_module: Any, litellm_model: str) -> tuple[Any, Any]:
    """Best-effort lookup of (input_cost_per_token, output_cost_per_token).

    LiteLLM keys its ``model_cost`` table sometimes with the bare model
    id (e.g. ``"gpt-5"``) and sometimes with the prefixed id
    (``"openai/gpt-5"``). We try both and the lower-cased variants.
    Returns ``(None, None)`` if no entry matches — the runner keeps
    working without unit pricing in that case.
    """
    table = getattr(litellm_module, "model_cost", None)
    if not isinstance(table, dict):
        return None, None
    bare = litellm_model.split("/", 1)[-1]
    candidates = [litellm_model, bare, litellm_model.lower(), bare.lower()]
    for key in candidates:
        entry = table.get(key)
        if isinstance(entry, dict):
            return (
                entry.get("input_cost_per_token"),
                entry.get("output_cost_per_token"),
            )
    return None, None


def format_cost_inline(metrics: dict[str, Any]) -> str:
    """Render the per-call telemetry tail printed after PASS/FAIL."""
    pt = metrics.get("prompt_tokens")
    ct = metrics.get("completion_tokens")
    cost = metrics.get("cost_usd")
    parts = []
    if pt is not None and ct is not None:
        parts.append(f"in={pt} out={ct}")
    elif (tt := metrics.get("total_tokens")) is not None:
        parts.append(f"tokens={tt}")
    if cost is not None:
        parts.append(f"cost=${cost:.4f}")
    return "  ".join(parts) if parts else ""


def print_batch_summary(
    rows: list[dict[str, Any]], passed: int, failed: int
) -> None:
    """Aggregate and pretty-print token / cost totals after the run loop."""
    print(
        f"\nDone. {COLOR_GREEN}{passed} passed{COLOR_RESET}, "
        f"{COLOR_RED if failed else COLOR_GREEN}{failed} failed{COLOR_RESET}."
    )
    if not rows:
        return

    total_in = sum(int(r["prompt_tokens"]) for r in rows if r["prompt_tokens"] != "")
    total_out = sum(int(r["completion_tokens"]) for r in rows if r["completion_tokens"] != "")
    total_cost = sum(
        float(r["cost_usd"]) for r in rows if r["cost_usd"] != ""
    )
    rows_with_cost = sum(1 for r in rows if r["cost_usd"] != "")
    rows_without_cost = len(rows) - rows_with_cost

    print(
        f"Tokens: {total_in:,} in / {total_out:,} out / "
        f"{total_in + total_out:,} total."
    )
    if rows_with_cost:
        cost_str = f"Cost: ${total_cost:.4f} ({rows_with_cost}/{len(rows)} call(s) priced"
        if rows_without_cost:
            cost_str += f"; {rows_without_cost} missing pricing data"
        cost_str += ")."
        print(cost_str)

        per_subject: dict[str, float] = {}
        for r in rows:
            if r["cost_usd"] != "":
                per_subject[r["subject_id"]] = (
                    per_subject.get(r["subject_id"], 0.0) + float(r["cost_usd"])
                )
        if len(per_subject) > 1:
            breakdown = ", ".join(
                f"{sid}: ${cost:.4f}"
                for sid, cost in sorted(per_subject.items())
            )
            print(f"Cost by subject: {breakdown}.")
    else:
        print(
            f"{COLOR_YELLOW}WARN{COLOR_RESET} no cost data available "
            f"(LiteLLM may lack pricing for the model(s) used)."
        )


def write_batch_log(repo_root: Path, rows: list[dict[str, Any]]) -> None:
    """Persist per-call telemetry to logs/batch_logs/<utc>.csv (gitignored)."""
    if not rows:
        return
    log_dir = repo_root / "logs" / "batch_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    log_path = log_dir / f"{stamp}.csv"
    with log_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=BATCH_LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Batch log: {log_path.relative_to(repo_root)}")
