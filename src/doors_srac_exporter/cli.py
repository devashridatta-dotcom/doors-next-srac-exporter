"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .exporter import ValidationError, export_document, validate_document


def _load_json(path: str) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only DOORS Next SRAC reference exporter")
    parser.add_argument("--config", help="JSON export configuration")
    parser.add_argument("--input", help="Normalized Reportable REST response JSON")
    parser.add_argument("--output", help="Destination SRAC interchange document")
    parser.add_argument("--validate", help="Validate an existing SRAC interchange document")
    args = parser.parse_args()
    try:
        if args.validate:
            validate_document(_load_json(args.validate))
            print(f"Valid: {args.validate}")
            return 0
        if not (args.config and args.input and args.output):
            parser.error("--config, --input, and --output are required for export")
        document = export_document(_load_json(args.config), _load_json(args.input))
        Path(args.output).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

