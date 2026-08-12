"""OpenAPI export."""

from __future__ import annotations

import json
from pathlib import Path

from app.export_openapi import export, main


def test_export_writes_a_document_describing_the_public_routes(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "openapi.json"
    export(destination)

    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["openapi"].startswith("3.")
    assert document["info"]["title"] == "Security+ Study API"
    assert {"/healthz", "/api/catalog", "/api/questions"} <= set(document["paths"])


def test_export_never_advertises_an_answer_field(tmp_path: Path) -> None:
    destination = tmp_path / "openapi.json"
    export(destination)
    schema = json.loads(destination.read_text(encoding="utf-8"))["components"]["schemas"]
    assert "answer" not in schema["QuestionSummary"]["properties"]


def test_main_accepts_a_destination_argument(tmp_path: Path) -> None:
    destination = tmp_path / "openapi.json"
    assert main([str(destination)]) == 0
    assert destination.exists()
