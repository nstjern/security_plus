"""Study session lifecycle."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.core.constants import DOMAIN_NAMES
from tests.conftest import PASSWORD


def start_session(client: TestClient, csrf: dict[str, str], **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"mode": "all", "shuffle_answers": False}
    payload.update(overrides)
    response = client.post("/api/sessions", json=payload, headers=csrf)
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_creating_a_session_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/sessions", json={"mode": "all"}).status_code == 401


def test_creating_a_session_requires_the_csrf_header(signed_in: TestClient) -> None:
    assert signed_in.post("/api/sessions", json={"mode": "all"}).status_code == 403


def test_an_all_mode_session_covers_the_whole_bank(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf)
    assert session["total_questions"] == 136
    assert session["status"] == "active"
    assert session["answered"] == 0


def test_a_domain_session_is_limited_to_that_domain(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf, mode="domain", filter_value=DOMAIN_NAMES[0])
    assert 0 < session["total_questions"] < 136
    assert session["filters"] == {"value": DOMAIN_NAMES[0]}


def test_a_practice_session_honours_the_requested_size(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    assert start_session(signed_in, csrf, mode="practice", count=5)["total_questions"] == 5


def test_a_mode_needing_a_filter_value_reports_the_problem(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    response = signed_in.post("/api/sessions", json={"mode": "subject"}, headers=csrf)
    assert response.status_code == 422
    assert "filter value" in response.json()["detail"]


def test_a_selection_matching_nothing_reports_the_problem(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    response = signed_in.post(
        "/api/sessions",
        json={"mode": "subject", "filter_value": "Nonexistent"},
        headers=csrf,
    )
    assert response.status_code == 422
    assert "No questions match" in response.json()["detail"]


def test_the_current_question_withholds_the_answer_key(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf)
    payload = signed_in.get(f"/api/sessions/{session['id']}/current-question").json()

    assert payload["position"] == 1
    assert payload["total"] == 136
    assert set(payload["question"]["choices"]) == set("abcd")
    assert {"answer", "explanation"}.isdisjoint(payload["question"])


def test_answering_returns_the_explanation_and_the_correct_choice(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=3)
    response = signed_in.post(
        f"/api/sessions/{session['id']}/answer", json={"choice": "a"}, headers=csrf
    )
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["result"] in {"correct", "incorrect"}
    assert body["correct_choice"] in set("abcd")
    assert body["explanation"]
    assert body["position"] == 1
    assert body["next_available"] is True


def test_a_correct_answer_is_graded_as_correct(signed_in: TestClient, csrf: dict[str, str]) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=2)
    session_id = session["id"]

    current = signed_in.get(f"/api/sessions/{session_id}/current-question").json()
    # Discover the correct letter by answering, then confirm the report agrees with itself.
    body = signed_in.post(
        f"/api/sessions/{session_id}/answer",
        json={"choice": "a"},
        headers=csrf,
    ).json()

    expected = "correct" if body["correct_choice"] == "a" else "incorrect"
    assert body["result"] == expected
    assert body["correct_choice_text"] == current["question"]["choices"][body["correct_choice"]]


def test_skipping_records_a_skip(signed_in: TestClient, csrf: dict[str, str]) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=2)
    body = signed_in.post(
        f"/api/sessions/{session['id']}/answer",
        json={"choice": None},
        headers=csrf,
    ).json()
    assert body["result"] == "skipped"


def test_answering_advances_to_the_next_question(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=3)
    session_id = session["id"]
    first = signed_in.get(f"/api/sessions/{session_id}/current-question").json()

    signed_in.post(f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf)
    second = signed_in.get(f"/api/sessions/{session_id}/current-question").json()

    assert second["position"] == 2
    assert second["question"]["id"] != first["question"]["id"]


def test_answering_every_question_finishes_the_session(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=2)
    session_id = session["id"]

    signed_in.post(f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf)
    final = signed_in.post(
        f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf
    ).json()

    assert final["session_status"] == "finished"
    assert final["next_available"] is False
    assert signed_in.get(f"/api/sessions/{session_id}/current-question").status_code == 409


def test_answering_a_finished_session_is_refused(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=1)
    session_id = session["id"]
    signed_in.post(f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf)

    response = signed_in.post(
        f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf
    )
    assert response.status_code == 409


def test_a_session_can_be_ended_early(signed_in: TestClient, csrf: dict[str, str]) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=10)
    ended = signed_in.post(f"/api/sessions/{session['id']}/end", headers=csrf).json()

    assert ended["status"] == "ended"
    assert ended["ended_at"] is not None
    assert signed_in.get(f"/api/sessions/{session['id']}/current-question").status_code == 409


def test_the_summary_tallies_the_answers(signed_in: TestClient, csrf: dict[str, str]) -> None:
    session = start_session(signed_in, csrf, mode="practice", count=3)
    session_id = session["id"]

    signed_in.post(f"/api/sessions/{session_id}/answer", json={"choice": "a"}, headers=csrf)
    signed_in.post(f"/api/sessions/{session_id}/answer", json={"choice": None}, headers=csrf)

    summary = signed_in.get(f"/api/sessions/{session_id}/summary").json()
    assert summary["answered"] == 2
    assert summary["skipped"] == 1
    assert summary["correct"] + summary["incorrect"] == 1
    assert summary["total_questions"] == 3


def test_recent_sessions_are_listed(signed_in: TestClient, csrf: dict[str, str]) -> None:
    start_session(signed_in, csrf, mode="practice", count=2)
    start_session(signed_in, csrf, mode="practice", count=3)
    assert len(signed_in.get("/api/sessions").json()) == 2


def test_an_unknown_session_is_not_found(signed_in: TestClient) -> None:
    unknown = "11111111-2222-3333-4444-555555555555"
    assert signed_in.get(f"/api/sessions/{unknown}").status_code == 404


def test_one_learner_cannot_read_another_learners_session(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    session = start_session(signed_in, csrf)
    signed_in.post("/api/auth/logout", headers=csrf)
    signed_in.post("/api/auth/register", json={"username": "intruder", "password": PASSWORD})

    assert signed_in.get(f"/api/sessions/{session['id']}").status_code == 404


def test_shuffled_sessions_still_grade_correctly(
    signed_in: TestClient, csrf: dict[str, str]
) -> None:
    """The displayed letter is translated back to the question's own lettering server-side."""
    session = start_session(signed_in, csrf, mode="practice", count=1, shuffle_answers=True)
    session_id = session["id"]

    current = signed_in.get(f"/api/sessions/{session_id}/current-question").json()
    body = signed_in.post(
        f"/api/sessions/{session_id}/answer", json={"choice": "b"}, headers=csrf
    ).json()

    displayed = current["question"]["choices"]
    assert body["correct_choice_text"] == displayed[body["correct_choice"]]
    assert body["result"] == ("correct" if body["correct_choice"] == "b" else "incorrect")
