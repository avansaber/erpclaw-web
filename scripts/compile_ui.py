#!/usr/bin/env python3
"""
compile_ui.py — Compile UI.yaml files into TypeScript mock data for erpclaw-web.

Takes a validated UI.yaml and produces a TypeScript file that conforms to VerticalLayout.
This is the bridge between module configs (YAML) and the Svelte frontend (TypeScript).

Usage:
  python scripts/compile_ui.py path/to/UI.yaml --out src/lib/mock/output.ts
  python scripts/compile_ui.py path/to/UI.yaml  # prints to stdout

Requires: pip install pyyaml
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: Install dependencies: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def yaml_to_ts(data: dict) -> str:
    """Convert a UI.yaml dict to a TypeScript VerticalLayout export."""
    name = data["name"]

    # Build the TypeScript object as JSON first, then format
    layout = {
        "name": data["name"],
        "label": data["label"],
        "description": data["description"],
        "icon": data["icon"],
        "color": data["color"],
        "kpis": data["kpis"],
        "workflows": data["workflows"],
        "sidebar": data["sidebar"],
        "entities": _compile_entities(data["entities"]),
        "attention": data.get("attention", []),
        "activity": data.get("activity", []),
    }

    # Convert to pretty JSON then transform to TS syntax
    json_str = json.dumps(layout, indent="\t", ensure_ascii=False)

    # Build TypeScript file
    lines = [
        "import type { VerticalLayout } from '$lib/types';",
        "",
        f"export const {name}: VerticalLayout = {json_str};",
        "",
    ]

    return "\n".join(lines)


def _compile_entities(entities: dict) -> dict:
    """Process entity definitions, preserving structure."""
    result = {}
    for key, entity in entities.items():
        compiled = {
            "label": entity["label"],
            "labelPlural": entity["labelPlural"],
            "columns": entity["columns"],
            "filters": entity.get("filters", []),
            "createForm": entity["createForm"],
        }
        if "statusColors" in entity:
            compiled["statusColors"] = entity["statusColors"]
        if "detailSections" in entity:
            compiled["detailSections"] = entity["detailSections"]
        if "actions" in entity:
            compiled["actions"] = entity["actions"]
        result[key] = compiled
    return result


def main():
    parser = argparse.ArgumentParser(description="Compile UI.yaml to TypeScript")
    parser.add_argument("file", help="UI.yaml file to compile")
    parser.add_argument("--out", "-o", help="Output TypeScript file path")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation before compiling")
    args = parser.parse_args()

    filepath = Path(args.file)

    try:
        with open(filepath) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if data is None:
        print("File is empty", file=sys.stderr)
        sys.exit(1)

    # Optionally validate first
    if args.validate:
        from validate_ui import load_schema, validate_file
        schema = load_schema()
        errors = validate_file(filepath, schema)
        if errors:
            print(f"Validation failed for {filepath}:", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)
            sys.exit(1)

    ts_output = yaml_to_ts(data)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(ts_output)
        print(f"Compiled {filepath} -> {out_path}")
    else:
        print(ts_output)


if __name__ == "__main__":
    main()
