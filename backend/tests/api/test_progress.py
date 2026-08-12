"""Cumulative progress and the personalized review guide."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def answer_until_incorrect(client: TestClient, csrf: dict[str, str]) -> dict[str, Any]:
    """Work through a session until one answer is graded incorrect, then return it.

    The question bank is authored, not generated, so the only reliable way to produce a
    miss is to answer and observe the grading.
    """
    created = client.post(
        "/api/sessions",
        json={"mode": "all", "shuffle_answers": False},
        headers=csrf,
    ).json()
    session_id = created["id"]

    for _ in range(created["total_questions"]):
        body = client.post(
            f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf
        ).json()
        if body["result"] == "incorrect":
            return body

    raise AssertionError("expected at least one incorrect answer")


def test_progress_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/progress/summary").status_code == 401
    assert client.get("/api/progress/missed").status_code == 401
    assert client.get("/api/review-guide").status_code == 401


def test_a_new_learner_has_an_empty_summary(signed_in: TestClient) -> None:
    summary = signed_in.get("/api/progress/summary").json()
    assert summary["attempts"] == 0
    assert summary["graded"] == 0
    assert summary["accuracy"] == 0.0
    assert summary["domains"] == []


def test_a_new_learner_has_missed_nothing(signed_in: TestClient) -> None:
    assert signed_in.get("/api/progress/missed").json() == {"count": 0, "question_ids": []}


def test_a_new_learners_review_guide_is_empty(signed_in: TestClient) -> None:
    guide = signed_in.get("/api/review-guide").json()
    assert guide["focus_areas"] == []
    assert guide["priority_domains"] == []


def test_answering_updates_the_cumulative_summary(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    created = signed_in.post(
        "/api/sessions", json={"mode": "practice", "count": 3}, headers=csrf
    ).json()
    signed_in.post(f"/api/sessions/{created['id']}/answer", json={"choice": "a"}, headers=csrf)

    summary = signed_in.get("/api/progress/summary").json()
    assert summary["attempts"] == 1
    assert summary["graded"] == 1
    assert len(summary["domains"]) == 1


def test_skipped_questions_count_as_attempts_but_are_not_graded(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    created = signed_in.post(
        "/api/sessions", json={"mode": "practice", "count": 2}, headers=csrf
    ).json()
    signed_in.post(f"/api/sessions/{created['id']}/answer", json={"choice": None}, headers=csrf)

    summary = signed_in.get("/api/progress/summary").json()
    assert summary["attempts"] == 1
    assert summary["skipped"] == 1
    assert summary["graded"] == 0


def test_a_missed_question_appears_in_the_missed_list(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    answer_until_incorrect(signed_in, csrf)
    missed = signed_in.get("/api/progress/missed").json()
    assert missed["count"] >= 1
    assert all(question_id.startswith("clean-") for question_id in missed["question_ids"])


def test_weakest_subjects_are_reported(signed_in: TestClient, csrf: dict[str, str]) -> None:
    answer_until_incorrect(signed_in, csrf)
    subjects = signed_in.get("/api/progress/subjects", params={"limit": 5}).json()

    assert subjects
    assert len(subjects) <= 5
    accuracies = [subject["accuracy"] for subject in subjects]
    assert accuracies == sorted(accuracies)


def test_the_review_guide_explains_every_missed_concept(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    answer_until_incorrect(signed_in, csrf)
    guide = signed_in.get("/api/review-guide").json()

    assert guide["focus_areas"]
    assert guide["priority_domains"]
    assert guide["total_incorrect"] >= 1

    concept = guide["focus_areas"][0]["concepts"][0]
    assert concept["explanation"]
    assert concept["objective"]
    assert concept["chapter"]
    assert concept["correct_choice"]


def test_the_review_guide_can_be_capped(signed_in: TestClient, csrf: dict[str, str]) -> None:
    answer_until_incorrect(signed_in, csrf)
    guide = signed_in.get("/api/review-guide", params={"max_focus_areas": 1}).json()
    assert len(guide["focus_areas"]) == 1


def test_a_missed_question_session_revisits_those_questions(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    answer_until_incorrect(signed_in, csrf)
    missed = signed_in.get("/api/progress/missed").json()

    created = signed_in.post("/api/sessions", json={"mode": "missed"}, headers=csrf)
    assert created.status_code == 201
    assert created.json()["total_questions"] == missed["count"]


def test_progress_is_private_to_each_learner(signed_in: TestClient, csrf: dict[str, str]) -> None:
    answer_until_incorrect(signed_in, csrf)
    signed_in.post("/api/auth/logout", headers=csrf)
    signed_in.post(
        "/api/auth/register",
        json={"username": "someone.else", "password": "another-long-password"},
    )

    assert signed_in.get("/api/progress/summary").json()["attempts"] == 0
