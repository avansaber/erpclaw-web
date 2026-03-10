#!/usr/bin/env python3
"""
validate_ui.py — Validate UI.yaml files against the v2 JSON schema.

Usage:
  python scripts/validate_ui.py path/to/UI.yaml [path/to/UI.yaml ...]
  python scripts/validate_ui.py --all  # Validate all UI.yaml files in src/

Requires: pip install jsonschema pyyaml
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml
    import jsonschema
except ImportError:
    print("ERROR: Install dependencies: pip install jsonschema pyyaml", file=sys.stderr)
    sys.exit(1)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "ui-yaml-v2.json"
SRC_ROOT = Path(__file__).parent.parent.parent / "src"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_file(filepath: Path, schema: dict) -> list[str]:
    """Validate a single UI.yaml file. Returns list of error messages."""
    errors = []

    try:
        with open(filepath) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]
    except FileNotFoundError:
        return [f"File not found: {filepath}"]

    if data is None:
        return ["File is empty"]

    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  {path}: {error.message}")

    # Cross-reference checks (beyond JSON schema)
    if isinstance(data, dict):
        errors.extend(_cross_checks(data))

    return errors


def _cross_checks(data: dict) -> list[str]:
    """Semantic validations that JSON schema can't express."""
    errors = []
    entities = data.get("entities", {})
    sidebar = data.get("sidebar", [])

    # Every entity must appear in sidebar
    sidebar_keys = set()
    for group in sidebar:
        for item in group.get("items", []):
            sidebar_keys.add(item.get("key", ""))

    for key in entities:
        if key not in sidebar_keys:
            errors.append(f"  entity '{key}' not referenced in sidebar")

    # Every entity must have at least one primary column
    for key, entity in entities.items():
        columns = entity.get("columns", [])
        if not any(c.get("primary") for c in columns):
            errors.append(f"  entity '{key}': no primary column defined")

    # Status filters should match statusColors keys
    for key, entity in entities.items():
        filters = entity.get("filters", [])
        status_colors = entity.get("statusColors", {})
        if status_colors:
            for f in filters:
                if f not in status_colors:
                    errors.append(f"  entity '{key}': filter '{f}' has no statusColor")

    # Form field names should be unique within entity
    for key, entity in entities.items():
        form = entity.get("createForm", {})
        seen_fields = set()
        for section in form.get("sections", []):
            for field in section.get("fields", []):
                fname = field.get("name", "")
                if fname in seen_fields:
                    errors.append(f"  entity '{key}': duplicate form field '{fname}'")
                seen_fields.add(fname)

    return errors


def find_all_ui_yamls() -> list[Path]:
    """Find all UI.yaml files under src/."""
    if not SRC_ROOT.exists():
        return []
    return sorted(SRC_ROOT.rglob("UI.yaml"))


def main():
    parser = argparse.ArgumentParser(description="Validate UI.yaml files against v2 schema")
    parser.add_argument("files", nargs="*", help="UI.yaml files to validate")
    parser.add_argument("--all", action="store_true", help="Validate all UI.yaml files in src/")
    args = parser.parse_args()

    schema = load_schema()

    if args.all:
        files = find_all_ui_yamls()
        if not files:
            print("No UI.yaml files found in src/")
            sys.exit(0)
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    total_errors = 0
    passed = 0
    failed = 0

    for filepath in files:
        errors = validate_file(filepath, schema)
        if errors:
            print(f"FAIL {filepath}")
            for e in errors:
                print(e)
            print()
            failed += 1
            total_errors += len(errors)
        else:
            print(f"PASS {filepath}")
            passed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed, {total_errors} errors")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
