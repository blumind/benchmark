#!/usr/bin/env python3
"""Aggregate per-call telemetry into operational metrics tables.

Reads every CSV under `logs/batch_logs/` (the gitignored telemetry trail
written by `run_evaluation.py`) and produces two deterministic tables
under `results/`:

    operational_per_subject.csv    one row per (subject_id, subject_version)
    operational_per_family.csv     one row per (subject_id, subject_version, family)

Only successful runs (``status == "pass"``) are considered, on the
principle that operational characteristics describe what to expect from
a *valid* response. Failed calls are out-of-distribution noise.

Operational metrics are decoupled from quality metrics (Pass rate,
Brier, ECE, Q_final → see `compute_metrics.py`). The two leaderboards
share `subject_id` as a join key but answer different questions:

    metrics_per_subject.csv       → "Is the model good at diagnosing?"
    operational_per_subject.csv   → "Is the model practical to use?"

Unit pricing (`price_per_input_token_usd`, `price_per_output_token_usd`)
is published as the rate at run time, captured per call in
`_runner_telemetry.py`. Aggregating it here surfaces the price the
benchmark version was actually run under, even if the provider changes
rates afterwards. Absolute USD spend is intentionally NOT published.

Exit codes:
    0  Operational tables written (or no successful runs found yet).
    2  Inputs missing or invalid arguments.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _validator_common import (  # noqa: E402
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    find_repo_root,
)


PER_SUBJECT_FIELDS = [
    "subject_id", "subject_version", "n_runs",
    "mean_input_tokens", "mean_output_tokens", "output_to_input_ratio",
    "median_latency_s", "p95_latency_s",
    "price_per_input_token_usd", "price_per_output_token_usd",
]

PER_FAMILY_FIELDS = [
    "subject_id", "subject_version", "family", "n_runs",
    "mean_input_tokens", "mean_output_tokens", "output_to_input_ratio",
    "median_latency_s", "p95_latency_s",
    "price_per_input_token_usd", "price_per_output_token_usd",
]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_batch_logs(repo_root: Path) -> list[dict[str, str]]:
    """Concatenate every CSV under logs/batch_logs/ into a single row stream."""
    log_dir = repo_root / "logs" / "batch_logs"
    if not log_dir.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(log_dir.glob("*.csv")):
        with path.open(newline="") as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def family_of(case_id: str) -> str:
    parts = case_id.split("-")
    return parts[1] if len(parts) >= 2 else ""


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def filter_usable(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep only rows with status=pass and the numeric fields we need."""
    out: list[dict[str, str]] = []
    for r in rows:
        if r.get("status") != "pass":
            continue
        try:
            int(r["prompt_tokens"])
            int(r["completion_tokens"])
            int(r["latency_ms"])
        except (ValueError, KeyError, TypeError):
            continue
        out.append(r)
    return out


def percentile_95(values: list[float]) -> float:
    """Linear-interpolation p95 robust to small samples (n < 20)."""
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_vals = sorted(values)
    rank = 0.95 * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def stats_for_group(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Compute the operational statistics for one group of rows."""
    ins = [int(r["prompt_tokens"]) for r in rows]
    outs = [int(r["completion_tokens"]) for r in rows]
    lat_ms = [int(r["latency_ms"]) for r in rows]
    prices_in = [
        float(r["price_per_input_token_usd"])
        for r in rows
        if r.get("price_per_input_token_usd")
    ]
    prices_out = [
        float(r["price_per_output_token_usd"])
        for r in rows
        if r.get("price_per_output_token_usd")
    ]

    mean_in = sum(ins) / len(ins)
    mean_out = sum(outs) / len(outs)
    ratio = (mean_out / mean_in) if mean_in else 0.0
    median_lat_s = statistics.median(lat_ms) / 1000.0
    p95_lat_s = percentile_95([float(x) for x in lat_ms]) / 1000.0
    mean_price_in = (sum(prices_in) / len(prices_in)) if prices_in else None
    mean_price_out = (sum(prices_out) / len(prices_out)) if prices_out else None

    return {
        "n_runs": len(rows),
        "mean_input_tokens": f"{mean_in:.1f}",
        "mean_output_tokens": f"{mean_out:.1f}",
        "output_to_input_ratio": f"{ratio:.3f}",
        "median_latency_s": f"{median_lat_s:.2f}",
        "p95_latency_s": f"{p95_lat_s:.2f}",
        "price_per_input_token_usd": (
            f"{mean_price_in:.10f}" if mean_price_in is not None else ""
        ),
        "price_per_output_token_usd": (
            f"{mean_price_out:.10f}" if mean_price_out is not None else ""
        ),
    }


def aggregate_per_subject(
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        grouped[(r["subject_id"], r["subject_version"])].append(r)

    out: list[dict[str, Any]] = []
    for (subject_id, subject_version), group in sorted(grouped.items()):
        row: dict[str, Any] = {
            "subject_id": subject_id,
            "subject_version": subject_version,
        }
        row.update(stats_for_group(group))
        out.append(row)
    return out


def aggregate_per_family(
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        family = family_of(r["case_id"])
        if not family:
            continue
        grouped[(r["subject_id"], r["subject_version"], family)].append(r)

    out: list[dict[str, Any]] = []
    for (subject_id, subject_version, family), group in sorted(grouped.items()):
        row: dict[str, Any] = {
            "subject_id": subject_id,
            "subject_version": subject_version,
            "family": family,
        }
        row.update(stats_for_group(group))
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-row progress (only the final summary is printed).",
    )
    args = parser.parse_args(argv[1:])

    repo_root = find_repo_root()

    raw = load_batch_logs(repo_root)
    if not raw:
        print(
            f"{COLOR_YELLOW}No batch logs found under logs/batch_logs/. "
            f"Nothing to aggregate.{COLOR_RESET}"
        )
        return 0

    usable = filter_usable(raw)
    skipped = len(raw) - len(usable)
    if not usable:
        print(
            f"{COLOR_YELLOW}No usable rows ({len(raw)} total, {skipped} skipped — "
            f"no successful runs yet).{COLOR_RESET}"
        )
        # Still write empty headers so downstream tooling sees the contract.
        write_csv(
            repo_root / "results" / "operational_per_subject.csv",
            PER_SUBJECT_FIELDS, [],
        )
        write_csv(
            repo_root / "results" / "operational_per_family.csv",
            PER_FAMILY_FIELDS, [],
        )
        return 0

    per_subject = aggregate_per_subject(usable)
    per_family = aggregate_per_family(usable)

    out_subject = repo_root / "results" / "operational_per_subject.csv"
    out_family = repo_root / "results" / "operational_per_family.csv"
    write_csv(out_subject, PER_SUBJECT_FIELDS, per_subject)
    write_csv(out_family, PER_FAMILY_FIELDS, per_family)

    if not args.quiet:
        print(
            f"Read {len(raw)} log row(s); used {len(usable)} successful run(s) "
            f"(skipped {skipped})."
        )
        print(
            f"  → {out_subject.relative_to(repo_root)}  "
            f"({len(per_subject)} subject(s))"
        )
        print(
            f"  → {out_family.relative_to(repo_root)}  "
            f"({len(per_family)} (subject, family) pair(s))"
        )
    print(f"{COLOR_GREEN}Done.{COLOR_RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
