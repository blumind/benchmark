"""Shared utilities for BluMind Benchmark validators.

Each validator script imports from this module to keep schema loading,
data loading and reporting consistent. Not intended to be invoked
directly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator


COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the blumind-benchmark directory upwards from start (or cwd).

    Heuristic: the directory that contains 'system/schemas/v1.0'.
    """
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "system" / "schemas" / "v1.0").is_dir():
            return candidate
    raise SystemExit(
        "ERROR: could not locate the blumind-benchmark repo root "
        "(no 'system/schemas/v1.0' directory found upwards from cwd)."
    )


def load_schema(repo_root: Path, schema_name: str) -> dict[str, Any]:
    """Load and structurally validate a Draft-07 JSON Schema by name."""
    path = repo_root / "system" / "schemas" / "v1.0" / f"{schema_name}.schema.json"
    if not path.is_file():
        raise SystemExit(f"ERROR: schema not found at {path}")
    schema = json.loads(path.read_text())
    Draft7Validator.check_schema(schema)
    return schema


def load_data(path: Path) -> Any:
    """Load JSON or YAML, autodetected by extension."""
    text = path.read_text()
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def validate_against(data: Any, schema: dict[str, Any]) -> list[str]:
    """Return human-readable error strings (empty list = valid)."""
    validator = Draft7Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{loc}: {err.message}")
    return errors


def report_file(path: Path, errors: list[str]) -> bool:
    """Print PASS/FAIL for a single file. Return True iff valid."""
    try:
        rel = path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        rel = path
    if errors:
        print(f"{COLOR_RED}FAIL{COLOR_RESET}  {rel}")
        for e in errors:
            print(f"        - {e}")
        return False
    print(f"{COLOR_GREEN}PASS{COLOR_RESET}  {rel}")
    return True


def summary(passed: int, failed: int) -> int:
    """Print a final summary line and return the appropriate exit code."""
    total = passed + failed
    if total == 0:
        print(f"\n{COLOR_YELLOW}No files validated.{COLOR_RESET}")
        return 0
    if failed == 0:
        print(f"\n{COLOR_GREEN}{passed}/{total} files valid.{COLOR_RESET}")
        return 0
    print(f"\n{COLOR_RED}{failed}/{total} files failed validation.{COLOR_RESET}")
    return 1
