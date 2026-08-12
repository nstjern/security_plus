"""Write the generated OpenAPI document to disk.

Committing the result makes every API change visible in review, and lets CI fail when the
committed contract no longer matches the code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import create_app

DEFAULT_DESTINATION = Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"


def export(destination: Path) -> None:
    document = create_app().openapi()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    destination = Path(arguments[0]) if arguments else DEFAULT_DESTINATION
    export(destination)
    print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
