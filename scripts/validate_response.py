#!/usr/bin/env python3
"""Validate response JSON files against response.schema.json.

Default scope: every .json file under responses/ in the repo root.

Usage:
    python scripts/validate_response.py                   # validate all
    python scripts/validate_response.py path/to/file.json # validate one
    python scripts/validate_response.py path/to/dir       # validate dir tree

Cross-file invariants (beyond the schema):
    - The filename stem follows the convention <case_id>__<run_id>.json
      and matches the case_id and run_id inside the JSON.

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
    fname = path.stem
    if "__" in fname:
        case_part, _, run_part = fname.partition("__")
        if data.get("case_id") != case_part:
            extra.append(
                f"<filename>: case_id in JSON ({data.get('case_id')!r}) "
                f"does not match filename prefix ({case_part!r})"
            )
        if data.get("run_id") != run_part:
            extra.append(
                f"<filename>: run_id in JSON ({data.get('run_id')!r}) "
                f"does not match filename suffix ({run_part!r})"
            )
    return extra


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    schema = load_schema(repo_root, "response")

    explicit = len(argv) > 1
    target = Path(argv[1]) if explicit else repo_root / "responses"

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
