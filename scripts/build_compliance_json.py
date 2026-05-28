#!/usr/bin/env python3
"""Build-time: convert config/compliance_rules.yaml → config/compliance_rules.json.

The repo ships the .json file as the runtime artifact so the package has zero
runtime dependencies. PyYAML is a dev-only dependency used by this script and
by anyone authoring the YAML source.

CI verifies the JSON stays in sync with the YAML on every PR.

Usage:
    python scripts/build_compliance_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        print(
            "pyyaml not installed. Install with: pip install -e '.[dev]'",
            file=sys.stderr,
        )
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "config" / "compliance_rules.yaml"
    dst = repo_root / "config" / "compliance_rules.json"
    if not src.exists():
        print(f"missing source: {src}", file=sys.stderr)
        return 1

    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    dst.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {dst} ({dst.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
