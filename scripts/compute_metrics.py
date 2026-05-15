#!/usr/bin/env python3
"""Compute aggregated benchmark metrics from responses, scorings and golds.

Reads:
    responses/v1.0/<subject_id>/<case_id>__<run_id>.json
    scoring/v1.0/<subject_id>/<case_id>__<run_id>__eval-<reviewer_id>.json
    golds/v1.0/<case_id>_gold.md

Writes (deterministic, sorted):
    results/per_run.csv
    results/metrics_per_subject.csv
    results/metrics_per_family.csv

The formulas, justifications and binning conventions are defined in
`system/rubric/v1.0/aggregated_metrics.md`. Any change to a formula here
must be reflected in that file in the same commit, and vice versa.

This script does NOT re-validate the input artifacts against their JSON
Schemas — it assumes that the dedicated validators (validate_response.py,
validate_evaluation.py, validate_gold.py) have already been run. It does
fail loudly on cross-file inconsistencies (e.g. a scoring file with no
matching response, two scorings for the same triplet, missing gold).

Exit codes:
    0  Computation succeeded (possibly with warnings about empty inputs).
    1  Cross-file inconsistency detected; aborting to avoid silent garbage.
    2  Missing or unreadable input directory, or invalid CLI arguments.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from _validator_common import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    find_repo_root,
)


JSON_BLOCK_RE = re.compile(r"^```json\s*\n(.*?)^```", re.DOTALL | re.MULTILINE)

DEFAULT_ALPHA = 0.5
NUM_BINS_ECE = 10


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TripletKey:
    """Identifies a unique (case, subject, run) triplet."""
    case_id: str
    subject_id: str
    run_id: str


@dataclass
class PerRun:
    """One row per scored (case, subject, run, reviewer)."""
    subject_id: str
    subject_version: str
    case_id: str
    family: str
    run_id: str
    reviewer_id: str
    scoring_timestamp_utc: str
    rubric_floor: int
    rubric_ceiling: int
    raw_score: int
    clipped_score: int
    has_critical_fail: bool
    has_recoverable_fail: bool
    classification: str
    reported_confidence: int
    confidence_unit: float
    correctness: float


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_responses(repo_root: Path, version: str) -> dict[TripletKey, dict[str, Any]]:
    """Load every JSON under responses/<version>/<subject>/, excluding _errors/."""
    base = repo_root / "responses" / version
    out: dict[TripletKey, dict[str, Any]] = {}
    if not base.is_dir():
        return out
    for f in sorted(base.glob("*/*.json")):
        if "_errors" in f.parts:
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"ERROR: response {f} is not valid JSON: {exc}. "
                f"Run validate_response.py first."
            )
        key = TripletKey(
            case_id=data["case_id"],
            subject_id=data["subject_id"],
            run_id=data["run_id"],
        )
        if key in out:
            raise SystemExit(
                f"ERROR: duplicate response for {key} "
                f"(found in {out[key]['__path']} and {f}). "
                f"Responses are append-only; resolve manually."
            )
        data["__path"] = str(f.relative_to(repo_root))
        out[key] = data
    return out


def load_scorings(repo_root: Path, version: str) -> dict[TripletKey, list[dict[str, Any]]]:
    """Load every JSON under scoring/<version>/<subject>/, grouped by triplet."""
    base = repo_root / "scoring" / version
    out: dict[TripletKey, list[dict[str, Any]]] = defaultdict(list)
    if not base.is_dir():
        return out
    for f in sorted(base.glob("*/*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"ERROR: scoring {f} is not valid JSON: {exc}. "
                f"Run validate_evaluation.py first."
            )
        ref = data["response_ref"]
        key = TripletKey(
            case_id=ref["case_id"],
            subject_id=ref["subject_id"],
            run_id=ref["run_id"],
        )
        data["__path"] = str(f.relative_to(repo_root))
        out[key].append(data)
    return out


def load_golds(repo_root: Path, version: str) -> dict[str, dict[str, Any]]:
    """Load every gold under golds/<version>/, keyed by case_id."""
    base = repo_root / "golds" / version
    out: dict[str, dict[str, Any]] = {}
    if not base.is_dir():
        return out
    for f in sorted(base.glob("*_gold.md")):
        text = f.read_text()
        match = JSON_BLOCK_RE.search(text)
        if not match:
            raise SystemExit(
                f"ERROR: gold {f} has no ```json``` block. "
                f"Run validate_gold.py first."
            )
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"ERROR: gold {f} JSON block is not valid: {exc}."
            )
        case_id = data["case_id"]
        if case_id in out:
            raise SystemExit(
                f"ERROR: duplicate gold for {case_id} "
                f"(found in {out[case_id]['__path']} and {f})."
            )
        data["__path"] = str(f.relative_to(repo_root))
        out[case_id] = data
    return out


# ---------------------------------------------------------------------------
# Per-run derivation (formulas live in aggregated_metrics.md § 2)
# ---------------------------------------------------------------------------


def family_of(case_id: str) -> str:
    """Extract the FAMILY segment from a case_id of the form RO-<FAMILY>-<NNN>."""
    parts = case_id.split("-")
    if len(parts) < 2:
        raise ValueError(f"unexpected case_id format: {case_id!r}")
    return parts[1]


def derive_classification(
    clipped_score: int,
    has_critical: bool,
    has_recoverable: bool,
    rubric_floor: int,
) -> str:
    """Apply the order documented in generic_rubric.md § Classification thresholds."""
    if has_critical:
        return "Fail"
    if has_recoverable:
        return "Conditional"
    if clipped_score < rubric_floor:
        return "Fail"
    if clipped_score >= 10:
        return "Pass"
    if clipped_score >= 7:
        return "Conditional"
    return "Fail"


def derive_per_run(
    response: dict[str, Any],
    scoring: dict[str, Any],
    gold: dict[str, Any],
) -> PerRun:
    crit_scores = scoring["criterion_scores"]
    raw_score = sum(c["score"] for c in crit_scores.values())

    rubric_floor = int(gold.get("rubric_floor", 0))
    rubric_ceiling = int(gold.get("rubric_ceiling", 12))
    clipped_score = min(raw_score, rubric_ceiling)

    fails = scoring.get("automatic_fails_triggered", [])
    has_critical = any(f["severity"] == "critical" for f in fails)
    has_recoverable = any(f["severity"] == "recoverable" for f in fails)

    classification = derive_classification(
        clipped_score, has_critical, has_recoverable, rubric_floor
    )

    reported_confidence = int(response["confidence"])
    correctness = float(scoring["correctness"])

    return PerRun(
        subject_id=response["subject_id"],
        subject_version=response["subject_version"],
        case_id=response["case_id"],
        family=family_of(response["case_id"]),
        run_id=response["run_id"],
        reviewer_id=scoring["reviewer_id"],
        scoring_timestamp_utc=scoring["scoring_timestamp_utc"],
        rubric_floor=rubric_floor,
        rubric_ceiling=rubric_ceiling,
        raw_score=raw_score,
        clipped_score=clipped_score,
        has_critical_fail=has_critical,
        has_recoverable_fail=has_recoverable,
        classification=classification,
        reported_confidence=reported_confidence,
        confidence_unit=reported_confidence / 100.0,
        correctness=correctness,
    )


# ---------------------------------------------------------------------------
# Aggregations (formulas live in aggregated_metrics.md § 3, § 4)
# ---------------------------------------------------------------------------


def compute_brier(rows: list[PerRun]) -> float | None:
    """Soft Brier: BS = (1/N) Σ (p_i - o_i)^2, with o_i ∈ {0, 0.5, 1}."""
    if not rows:
        return None
    return sum((r.confidence_unit - r.correctness) ** 2 for r in rows) / len(rows)


def compute_ece(rows: list[PerRun], num_bins: int = NUM_BINS_ECE) -> float | None:
    """Soft ECE on `num_bins` fixed-width bins of width 1/num_bins over [0, 1]."""
    if not rows:
        return None
    n = len(rows)
    bins: list[list[PerRun]] = [[] for _ in range(num_bins)]
    for r in rows:
        cu = r.confidence_unit
        if cu >= 1.0:
            idx = num_bins - 1
        elif cu <= 0.0:
            idx = 0
        else:
            idx = int(cu * num_bins)
            if idx >= num_bins:
                idx = num_bins - 1
        bins[idx].append(r)
    ece = 0.0
    for bucket in bins:
        if not bucket:
            continue
        conf_b = sum(r.confidence_unit for r in bucket) / len(bucket)
        acc_b = sum(r.correctness for r in bucket) / len(bucket)
        ece += (len(bucket) / n) * abs(conf_b - acc_b)
    return ece


def compute_subject_metrics(
    subject_id: str,
    rows: list[PerRun],
    alpha: float,
) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {
            "subject_id": subject_id,
            "subject_version": "",
            "n_runs": 0,
            "n_pass": 0,
            "n_conditional": 0,
            "n_fail": 0,
            "n_critical_fails": 0,
            "n_recoverable_fails": 0,
            "pass_rate": "",
            "mean_clipped_score": "",
            "brier": "",
            "ece": "",
            "alpha": alpha,
            "q_final": "",
            "leaderboard_status": "NoData",
        }
    versions = sorted({r.subject_version for r in rows})
    n_pass = sum(1 for r in rows if r.classification == "Pass")
    n_cond = sum(1 for r in rows if r.classification == "Conditional")
    n_fail = sum(1 for r in rows if r.classification == "Fail")
    n_critical = sum(1 for r in rows if r.has_critical_fail)
    n_recoverable = sum(1 for r in rows if r.has_recoverable_fail)
    pass_rate = n_pass / n
    mean_clipped = sum(r.clipped_score for r in rows) / n
    brier = compute_brier(rows)
    ece = compute_ece(rows)
    q_final = alpha * pass_rate + (1.0 - alpha) * (mean_clipped / 12.0)
    disqualified = n_critical > 0
    return {
        "subject_id": subject_id,
        "subject_version": ", ".join(versions),
        "n_runs": n,
        "n_pass": n_pass,
        "n_conditional": n_cond,
        "n_fail": n_fail,
        "n_critical_fails": n_critical,
        "n_recoverable_fails": n_recoverable,
        "pass_rate": round(pass_rate, 4),
        "mean_clipped_score": round(mean_clipped, 4),
        "brier": round(brier, 4) if brier is not None else "",
        "ece": round(ece, 4) if ece is not None else "",
        "alpha": alpha,
        "q_final": round(q_final, 4),
        "leaderboard_status": "Disqualified" if disqualified else "Eligible",
    }


def compute_family_metrics(
    subject_id: str,
    family: str,
    rows: list[PerRun],
) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {
            "subject_id": subject_id,
            "family": family,
            "n_runs": 0,
            "n_pass": 0,
            "n_conditional": 0,
            "n_fail": 0,
            "pass_rate_family": "",
            "mean_clipped_score_family": "",
        }
    n_pass = sum(1 for r in rows if r.classification == "Pass")
    n_cond = sum(1 for r in rows if r.classification == "Conditional")
    n_fail = sum(1 for r in rows if r.classification == "Fail")
    return {
        "subject_id": subject_id,
        "family": family,
        "n_runs": n,
        "n_pass": n_pass,
        "n_conditional": n_cond,
        "n_fail": n_fail,
        "pass_rate_family": round(n_pass / n, 4),
        "mean_clipped_score_family": round(sum(r.clipped_score for r in rows) / n, 4),
    }


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------


PER_RUN_COLUMNS = [
    "subject_id", "subject_version",
    "case_id", "family",
    "run_id", "reviewer_id", "scoring_timestamp_utc",
    "rubric_floor", "rubric_ceiling",
    "raw_score", "clipped_score",
    "has_critical_fail", "has_recoverable_fail",
    "classification",
    "reported_confidence", "confidence_unit", "correctness",
]


SUBJECT_COLUMNS = [
    "subject_id", "subject_version",
    "n_runs", "n_pass", "n_conditional", "n_fail",
    "n_critical_fails", "n_recoverable_fails",
    "pass_rate", "mean_clipped_score",
    "brier", "ece",
    "alpha", "q_final",
    "leaderboard_status",
]


FAMILY_COLUMNS = [
    "subject_id", "family",
    "n_runs", "n_pass", "n_conditional", "n_fail",
    "pass_rate_family", "mean_clipped_score_family",
]


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in columns})


# ---------------------------------------------------------------------------
# Cross-file consistency
# ---------------------------------------------------------------------------


def check_consistency(
    responses: dict[TripletKey, dict[str, Any]],
    scorings: dict[TripletKey, list[dict[str, Any]]],
    golds: dict[str, dict[str, Any]],
    strict: bool,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors abort the run when strict=True."""
    errors: list[str] = []
    warnings: list[str] = []

    for key, sc_list in scorings.items():
        if len(sc_list) > 1:
            paths = ", ".join(sc["__path"] for sc in sc_list)
            errors.append(
                f"multiple scorings for {key}: {paths}. v1.0 expects exactly one "
                f"reviewer per (case, subject, run); run aggregate_scoring.py "
                f"first or consolidate manually."
            )
        if key not in responses:
            errors.append(
                f"scoring {sc_list[0]['__path']} references {key} but no matching "
                f"response was found under responses/."
            )
        if key.case_id not in golds:
            errors.append(
                f"scoring {sc_list[0]['__path']} references case {key.case_id} "
                f"but no matching gold was found under golds/."
            )

    for key, resp in responses.items():
        if key not in scorings:
            warnings.append(
                f"response {resp['__path']} has no scoring yet (will not appear "
                f"in aggregated metrics)."
            )

    if strict and warnings:
        errors.extend(warnings)
        warnings = []

    return errors, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--benchmark-version", default="v1.0",
        help="Benchmark version subdirectory to read (default: v1.0).",
    )
    parser.add_argument(
        "--output-dir", default="results",
        help="Output directory relative to the repo root (default: results).",
    )
    parser.add_argument(
        "--alpha", type=float, default=DEFAULT_ALPHA,
        help=f"Weight for pass_rate in Q_final (default: {DEFAULT_ALPHA}). "
             f"See aggregated_metrics.md § 3.5 before changing.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings (e.g. responses without scoring) as errors.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-row progress output.",
    )
    args = parser.parse_args(argv[1:])

    if not 0.0 <= args.alpha <= 1.0:
        print(f"ERROR: --alpha must be in [0, 1], got {args.alpha}", file=sys.stderr)
        return 2

    repo_root = find_repo_root()
    version = args.benchmark_version
    out_dir = repo_root / args.output_dir

    responses = load_responses(repo_root, version)
    scorings = load_scorings(repo_root, version)
    golds = load_golds(repo_root, version)

    if not args.quiet:
        print(
            f"Inputs: {len(responses)} response(s), "
            f"{sum(len(v) for v in scorings.values())} scoring(s) over "
            f"{len(scorings)} triplet(s), {len(golds)} gold(s) "
            f"under benchmark_version={version}."
        )

    errors, warnings = check_consistency(responses, scorings, golds, args.strict)
    for w in warnings:
        print(f"{COLOR_YELLOW}WARN{COLOR_RESET}  {w}")
    if errors:
        for e in errors:
            print(f"{COLOR_RED}ERROR{COLOR_RESET} {e}", file=sys.stderr)
        return 1

    per_run_rows: list[PerRun] = []
    for key, sc_list in scorings.items():
        scoring = sc_list[0]
        response = responses[key]
        gold = golds[key.case_id]
        per_run_rows.append(derive_per_run(response, scoring, gold))

    per_run_rows.sort(
        key=lambda r: (r.subject_id, r.case_id, r.run_id, r.reviewer_id)
    )

    write_csv(
        out_dir / "per_run.csv",
        PER_RUN_COLUMNS,
        [asdict(r) for r in per_run_rows],
    )

    by_subject: dict[str, list[PerRun]] = defaultdict(list)
    for r in per_run_rows:
        by_subject[r.subject_id].append(r)

    subject_rows = [
        compute_subject_metrics(sid, rows, args.alpha)
        for sid, rows in sorted(by_subject.items())
    ]
    write_csv(out_dir / "metrics_per_subject.csv", SUBJECT_COLUMNS, subject_rows)

    by_subject_family: dict[tuple[str, str], list[PerRun]] = defaultdict(list)
    for r in per_run_rows:
        by_subject_family[(r.subject_id, r.family)].append(r)

    family_rows = [
        compute_family_metrics(sid, fam, rows)
        for (sid, fam), rows in sorted(by_subject_family.items())
    ]
    write_csv(out_dir / "metrics_per_family.csv", FAMILY_COLUMNS, family_rows)

    if not args.quiet:
        print(
            f"\n{COLOR_GREEN}Done.{COLOR_RESET} "
            f"{len(per_run_rows)} per-run row(s), "
            f"{len(subject_rows)} subject row(s), "
            f"{len(family_rows)} (subject, family) row(s) "
            f"written under {out_dir.relative_to(repo_root)}/."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
