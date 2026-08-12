"""Catalog and question browsing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.constants import DOMAIN_NAMES

TOTAL_QUESTIONS = 136


def test_catalog_lists_every_filter_value(client: TestClient) -> None:
    payload = client.get("/api/catalog").json()
    assert payload["question_count"] == TOTAL_QUESTIONS
    assert set(DOMAIN_NAMES) <= set(payload["domains"])
    assert len(payload["chapters"]) == 17
    assert payload["subjects"]
    assert payload["objectives"]


def test_chapters_are_returned_in_numeric_order(client: TestClient) -> None:
    chapters = client.get("/api/catalog").json()["chapters"]
    assert chapters[0].startswith("Chapter 1:")
    assert chapters[-1].startswith("Chapter 17:")


def test_question_listing_is_paginated(client: TestClient) -> None:
    payload = client.get("/api/questions").json()
    assert payload["total"] == TOTAL_QUESTIONS
    assert payload["limit"] == 20
    assert len(payload["items"]) == 20


def test_pagination_window_moves_with_the_offset(client: TestClient) -> None:
    first = client.get("/api/questions", params={"limit": 5}).json()["items"]
    second = client.get("/api/questions", params={"limit": 5, "offset": 5}).json()["items"]
    assert {item["id"] for item in first}.isdisjoint({item["id"] for item in second})


def test_filtering_by_domain_narrows_the_result(client: TestClient) -> None:
    payload = client.get("/api/questions", params={"domain": DOMAIN_NAMES[2], "limit": 100}).json()
    assert 0 < payload["total"] < TOTAL_QUESTIONS
    assert all(item["domain"] == DOMAIN_NAMES[2] for item in payload["items"])


def test_unknown_filter_values_return_an_empty_page(client: TestClient) -> None:
    payload = client.get("/api/questions", params={"subject": "Nonexistent"}).json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_out_of_range_pagination_is_rejected(client: TestClient) -> None:
    assert client.get("/api/questions", params={"limit": 500}).status_code == 422
    assert client.get("/api/questions", params={"offset": -1}).status_code == 422


def test_reading_one_question_returns_its_metadata(client: TestClient) -> None:
    payload = client.get("/api/questions/clean-d01-q001").json()
    assert payload["id"] == "clean-d01-q001"
    assert payload["domain"] == DOMAIN_NAMES[0]
    assert set(payload["choices"]) == set("abcd")


def test_unknown_question_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/questions/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"


def test_answers_and_explanations_are_never_exposed_to_browsers(client: TestClient) -> None:
    """Answer keys are revealed only in response to a submitted answer."""
    single = client.get("/api/questions/clean-d01-q001").json()
    listing = client.get("/api/questions", params={"limit": 200}).json()

    leaked_fields = {"answer", "explanation", "correction_note", "corrected"}
    assert leaked_fields.isdisjoint(single)
    for item in listing["items"]:
        assert leaked_fields.isdisjoint(item)
