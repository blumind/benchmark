#!/usr/bin/env python3
"""Public-export safety gate for the BluMind Benchmark.

Some fields in this repository belong to the *commercial* (PREMIUM) tier of
the BluMind dataset and must NEVER end up in the public benchmark export
that is published on GitHub / blumind.dev. This script is the manual gate
that catches them before publication.

What it checks
--------------
For every reviewer-scoring file under `scoring/v1.0/**/*.json` and every
ideal-response file under `ideal_responses/v1.0/*.json`, the script flags
fields that are explicitly tagged as PREMIUM in their JSON Schema:

    scoring     → criterion_scores.*.justification_long
    ideal       → expert_chain_of_thought

`ideal_responses/v1.0/*.json` are also flagged as PREMIUM *as a whole*:
the schema is public, but the per-case files are not — they are the SFT
material that drives `sft.jsonl` in the commercial export.

Two modes
---------
Default (check):

    python scripts/check_public_safety.py

    Exit 0 → repo is safe to publish (no PREMIUM content found).
    Exit 1 → PREMIUM content found; the script prints a report listing
             every offending file and field path.

Export (sanitize to a public mirror):

    python scripts/check_public_safety.py --export public_export/

    Mirrors scoring/v1.0/ into public_export/scoring/v1.0/ with all
    PREMIUM fields stripped, and omits ideal_responses/ entirely. Other
    folders (cases/, responses/, results/, system/, subjects/, docs/...)
    are intentionally left to the caller — they are already public by
    construction; only the two PREMIUM-bearing trees need sanitization.

This script never deletes or modifies anything in scoring/, responses/ or
ideal_responses/. It is read-only on the source.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from _validator_common import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    find_repo_root,
)


PREMIUM_SCORING_FIELDS: tuple[str, ...] = ("justification_long",)
PREMIUM_IDEAL_FIELDS: tuple[str, ...] = ("expert_chain_of_thought",)


def _scan_scoring_file(path: Path) -> list[str]:
    """Return a list of dotted paths to PREMIUM fields found in a scoring JSON."""
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"<unreadable: {exc}>"]
    offenders: list[str] = []
    crits = data.get("criterion_scores")
    if isinstance(crits, dict):
        for crit_name, crit in crits.items():
            if not isinstance(crit, dict):
                continue
            for field in PREMIUM_SCORING_FIELDS:
                if field in crit and crit[field]:
                    offenders.append(f"criterion_scores.{crit_name}.{field}")
    return offenders


def _scan_ideal_file(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"<unreadable: {exc}>"]
    offenders: list[str] = []
    for field in PREMIUM_IDEAL_FIELDS:
        if field in data and data[field]:
            offenders.append(field)
    return offenders


def _strip_scoring(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of a scoring object with all PREMIUM fields removed."""
    out = json.loads(json.dumps(data))
    crits = out.get("criterion_scores")
    if isinstance(crits, dict):
        for crit in crits.values():
            if not isinstance(crit, dict):
                continue
            for field in PREMIUM_SCORING_FIELDS:
                crit.pop(field, None)
    return out


def cmd_check(repo: Path) -> int:
    scoring_root = repo / "scoring" / "v1.0"
    ideal_root = repo / "ideal_responses" / "v1.0"

    scoring_offenders: list[tuple[Path, list[str]]] = []
    if scoring_root.is_dir():
        for path in sorted(scoring_root.rglob("*.json")):
            hits = _scan_scoring_file(path)
            if hits:
                scoring_offenders.append((path, hits))

    ideal_present: list[Path] = []
    ideal_field_offenders: list[tuple[Path, list[str]]] = []
    if ideal_root.is_dir():
        for path in sorted(ideal_root.glob("*.json")):
            ideal_present.append(path)
            hits = _scan_ideal_file(path)
            if hits:
                ideal_field_offenders.append((path, hits))

    print("BluMind public-safety check")
    print("===========================")
    print(f"repo root: {repo}")
    print(f"scoring files scanned:        {sum(1 for _ in scoring_root.rglob('*.json')) if scoring_root.is_dir() else 0}")
    print(f"ideal-response files present: {len(ideal_present)}")
    print()

    fail = False

    if scoring_offenders:
        fail = True
        print(f"{COLOR_RED}FAIL{COLOR_RESET}: PREMIUM fields found in scoring/v1.0/")
        for path, hits in scoring_offenders:
            rel = path.relative_to(repo)
            print(f"  - {rel}")
            for h in hits:
                print(f"      · {h}")
        print()

    if ideal_present:
        fail = True
        print(
            f"{COLOR_RED}FAIL{COLOR_RESET}: ideal_responses/v1.0/ contains files that must "
            f"not be published ({len(ideal_present)} file(s)):"
        )
        for path in ideal_present:
            print(f"  - {path.relative_to(repo)}")
        print(
            f"  {COLOR_YELLOW}note{COLOR_RESET}: the .gitignore rule keeps these out of git, "
            "but this script still flags them so you do not accidentally publish a tarball."
        )
        print()

    if ideal_field_offenders:
        for path, hits in ideal_field_offenders:
            rel = path.relative_to(repo)
            print(f"      · {rel}: {', '.join(hits)}")
        print()

    if fail:
        print(
            f"{COLOR_RED}NOT SAFE TO PUBLISH.{COLOR_RESET} "
            "Run with --export <dir> to produce a sanitized public mirror, "
            "or strip the PREMIUM fields manually."
        )
        return 1

    print(f"{COLOR_GREEN}OK{COLOR_RESET}: no PREMIUM content detected. Safe to publish.")
    return 0


def cmd_export(repo: Path, out_dir: Path) -> int:
    out_dir = out_dir.resolve()
    if out_dir == repo:
        print("ERROR: --export target cannot be the repo root.", file=sys.stderr)
        return 2

    scoring_root = repo / "scoring" / "v1.0"
    if not scoring_root.is_dir():
        print(f"ERROR: scoring root not found at {scoring_root}", file=sys.stderr)
        return 2

    out_scoring = out_dir / "scoring" / "v1.0"
    if out_scoring.exists():
        shutil.rmtree(out_scoring)
    out_scoring.mkdir(parents=True, exist_ok=True)

    written = 0
    stripped_files = 0
    stripped_fields = 0
    for path in sorted(scoring_root.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"  skip (unreadable): {path.relative_to(repo)} — {exc}", file=sys.stderr)
            continue
        hits_before = _scan_scoring_file(path)
        clean = _strip_scoring(data)
        target = out_scoring / path.relative_to(scoring_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n")
        written += 1
        if hits_before:
            stripped_files += 1
            stripped_fields += len(hits_before)

    print("BluMind public-safety export")
    print("============================")
    print(f"source:      {scoring_root.relative_to(repo)}")
    print(f"destination: {out_scoring}")
    print(f"files written: {written}")
    print(f"files with PREMIUM fields stripped: {stripped_files}")
    print(f"PREMIUM field instances removed:    {stripped_fields}")
    print()
    print(
        f"{COLOR_YELLOW}reminder{COLOR_RESET}: ideal_responses/ is intentionally NOT mirrored. "
        "Only the public schema (system/schemas/v1.0/ideal_response.schema.json) is publishable."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--export",
        metavar="DIR",
        type=Path,
        help="Sanitize scoring/v1.0/ into DIR/scoring/v1.0/ (PREMIUM fields stripped).",
    )
    args = parser.parse_args()

    repo = find_repo_root()

    if args.export is not None:
        return cmd_export(repo, args.export)
    return cmd_check(repo)


if __name__ == "__main__":
    sys.exit(main())
