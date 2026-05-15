#!/usr/bin/env python3
"""Validate ideal-response JSON files against ideal_response.schema.json.

Default scope: every .json file under ideal_responses/ in the repo root.

Usage:
    python scripts/validate_ideal_response.py                   # validate all
    python scripts/validate_ideal_response.py path/to/file.json # validate one
    python scripts/validate_ideal_response.py path/to/dir       # validate dir tree

Cross-file invariants (beyond the schema):
    - Filename stem matches the case_id (e.g. RO-FOUL-001_ideal.json → case_id RO-FOUL-001).
    - source_strategy='expert-curated-from-llm' or 'expert-pair-curated-from-llm'
      → seed_response_ref is required.
    - source_strategy='expert-authored' or 'expert-pair-authored'
      → seed_response_ref must be absent.
    - source_strategy='expert-pair-*' → at least 2 authors required.
    - status='review' or 'approved' → last_updated_at is required.

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
    extra: list[str] = []

    expected_case = path.stem.removesuffix("_ideal")
    if data.get("case_id") != expected_case:
        extra.append(
            f"<filename>: case_id ({data.get('case_id')!r}) "
            f"does not match filename stem ({expected_case!r}); "
            f"expected '<case_id>_ideal.json'."
        )

    strategy = data.get("source_strategy")
    has_seed = "seed_response_ref" in data
    if strategy in {"expert-curated-from-llm", "expert-pair-curated-from-llm"} and not has_seed:
        extra.append(
            f"source_strategy={strategy!r} requires 'seed_response_ref' to be present "
            f"(identifying the LLM response that was curated)."
        )
    if strategy in {"expert-authored", "expert-pair-authored"} and has_seed:
        extra.append(
            f"source_strategy={strategy!r} forbids 'seed_response_ref' "
            f"(scratch-written responses must not declare a seed)."
        )

    if strategy in {"expert-pair-authored", "expert-pair-curated-from-llm"}:
        if len(data.get("authors") or []) < 2:
            extra.append(
                f"source_strategy={strategy!r} requires at least 2 authors "
                f"(got {len(data.get('authors') or [])})."
            )

    if data.get("status") in {"review", "approved"} and "last_updated_at" not in data:
        extra.append(
            f"status={data.get('status')!r} requires 'last_updated_at' "
            f"(only 'draft' may omit it)."
        )

    return extra


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    schema = load_schema(repo_root, "ideal_response")

    explicit = len(argv) > 1
    target = Path(argv[1]) if explicit else repo_root / "ideal_responses"

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
