#!/usr/bin/env python3
"""Validate evaluation JSON files against evaluation.schema.json.

Default scope: every .json file under scoring/ in the repo root.

Usage:
    python scripts/validate_evaluation.py                   # validate all
    python scripts/validate_evaluation.py path/to/file.json # validate one
    python scripts/validate_evaluation.py path/to/dir       # validate dir tree

Cross-file invariants (beyond the schema):
    - The filename stem follows the convention
      <case_id>__<run_id>__eval-<reviewer_id>.json and matches the
      response_ref fields and reviewer_id inside the JSON.

Exit codes: 0 (all valid) or 1 (any failed).
"""

from __future__ import annotations

import sys
from pathlib import Path

from _validator_common import (
    find_repo_root,
    load_schema,
    load_data,
    validate_against,
    report_file,
    summary,
)


def cross_check(data: dict, path: Path) -> list[str]:
    extra = []
    parts = path.stem.split("__")
    if len(parts) < 3:
        return extra
    case_part, run_part, eval_part = parts[0], parts[1], parts[2]
    ref = data.get("response_ref", {}) or {}

    if ref.get("case_id") != case_part:
        extra.append(
            f"<filename>: response_ref.case_id ({ref.get('case_id')!r}) "
            f"does not match filename ({case_part!r})"
        )
    if ref.get("run_id") != run_part:
        extra.append(
            f"<filename>: response_ref.run_id ({ref.get('run_id')!r}) "
            f"does not match filename ({run_part!r})"
        )
    if eval_part.startswith("eval-"):
        reviewer_id_in_filename = eval_part[len("eval-"):]
        if data.get("reviewer_id") != reviewer_id_in_filename:
            extra.append(
                f"<filename>: reviewer_id ({data.get('reviewer_id')!r}) "
                f"does not match filename ({reviewer_id_in_filename!r})"
            )
    else:
        extra.append(
            f"<filename>: third segment must start with 'eval-' "
            f"(got {eval_part!r})"
        )
    return extra


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    schema = load_schema(repo_root, "evaluation")

    explicit = len(argv) > 1
    target = Path(argv[1]) if explicit else repo_root / "scoring"

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("*.json"))
    elif not explicit:
        print(f"Default target {target} does not exist; nothing to validate.")
        return 0
    else:
        print(f"ERROR: path not found: {target}", file=sys.stderr)
        return 2

    passed = failed = 0
    for f in files:
        try:
            data = load_data(f)
            errors = validate_against(data, schema) + cross_check(data, f)
        except Exception as exc:
            errors = [f"<load>: {exc}"]
        if report_file(f, errors):
            passed += 1
        else:
            failed += 1

    return summary(passed, failed)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
