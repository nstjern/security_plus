#!/usr/bin/env python3
"""Interactive, text-based Security+ study program."""

from __future__ import annotations

import json
import random
import shutil
import sys
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = APP_DIR / "questions.json"
PROGRESS_PATH = APP_DIR / "progress.json"
REVIEW_GUIDE_PATH = APP_DIR / "review_guide.txt"

DOMAIN_NAMES = [
    "Domain 1: General Security Concepts",
    "Domain 2: Threats, Vulnerabilities, and Mitigations",
    "Domain 3: Security Architecture",
    "Domain 4: Security Operations",
    "Domain 5: Security Program Management and Oversight",
]

# Fallback mappings for user-authored additions that omit explicit domain data.
CHAPTER_DOMAINS = {
    1: DOMAIN_NAMES[0],
    2: DOMAIN_NAMES[0],
    3: DOMAIN_NAMES[1],
    4: DOMAIN_NAMES[1],
    5: DOMAIN_NAMES[1],
    6: DOMAIN_NAMES[1],
    7: DOMAIN_NAMES[2],
    8: DOMAIN_NAMES[2],
    9: DOMAIN_NAMES[2],
    10: DOMAIN_NAMES[3],
    11: DOMAIN_NAMES[3],
    12: DOMAIN_NAMES[3],
    13: DOMAIN_NAMES[3],
    14: DOMAIN_NAMES[3],
    15: DOMAIN_NAMES[4],
    16: DOMAIN_NAMES[4],
    17: DOMAIN_NAMES[4],
}


def terminal_width() -> int:
    """Return a readable width even in very wide or narrow terminals."""
    return max(60, min(shutil.get_terminal_size(fallback=(88, 24)).columns, 100))


def clear_screen() -> None:
    """Clear an interactive terminal and return the cursor to the top."""
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="", flush=True)


def wrapped(text: str, *, indent: str = "", subsequent: str | None = None) -> str:
    """Wrap prose while preserving intentional paragraph and line breaks."""
    width = terminal_width()
    subsequent = indent if subsequent is None else subsequent
    lines: list[str] = []
    for raw_line in str(text).splitlines() or [""]:
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                raw_line.strip(),
                width=width,
                initial_indent=indent,
                subsequent_indent=subsequent,
                replace_whitespace=True,
            )
        )
    return "\n".join(lines)


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict[str, Any]]:
    """Load and minimally validate the question bank."""
    try:
        with path.open(encoding="utf-8") as question_file:
            questions = json.load(question_file)
    except FileNotFoundError as exc:
        raise SystemExit(f"Question bank not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Question bank is not valid JSON: {exc}") from exc

    if not isinstance(questions, list) or not questions:
        raise SystemExit("The question bank must be a non-empty JSON list.")

    required = {
        "id",
        "source_section",
        "grouping",
        "exam_domain",
        "objective",
        "subject",
        "question_number",
        "question",
        "choices",
        "answer",
        "explanation",
        "corrected",
        "correction_note",
        "provenance",
    }
    seen_ids: set[str] = set()
    for index, question in enumerate(questions, start=1):
        missing = required - question.keys()
        if missing:
            raise SystemExit(f"Question {index} is missing: {', '.join(sorted(missing))}")
        if question["id"] in seen_ids:
            raise SystemExit(f"Duplicate question ID: {question['id']}")
        seen_ids.add(question["id"])
        if question["answer"] not in question["choices"]:
            raise SystemExit(f"Invalid answer for question {question['id']}")

    return questions


def empty_progress() -> dict[str, Any]:
    return {"version": 1, "questions": {}}


def load_progress(path: Path = PROGRESS_PATH) -> dict[str, Any]:
    """Load saved progress; preserve a damaged file by refusing to overwrite it."""
    if not path.exists():
        return empty_progress()
    try:
        with path.open(encoding="utf-8") as progress_file:
            progress = json.load(progress_file)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Progress file is invalid and was not changed: {path}\n{exc}"
        ) from exc

    if not isinstance(progress, dict) or not isinstance(progress.get("questions"), dict):
        raise SystemExit(f"Progress file has an unsupported format: {path}")
    return progress


def save_progress(progress: dict[str, Any], path: Path = PROGRESS_PATH) -> None:
    """Save progress atomically to reduce the chance of a partial file."""
    temporary_path = path.with_suffix(".json.tmp")
    with temporary_path.open("w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, indent=2, ensure_ascii=False)
        progress_file.write("\n")
    temporary_path.replace(path)


def question_domain(question: dict[str, Any]) -> str:
    """Return a consistent exam domain for chapter and domain-bank questions."""
    if question.get("exam_domain"):
        return str(question["exam_domain"])
    grouping = question["grouping"]
    if grouping.startswith("Domain "):
        return grouping
    if grouping.startswith("Chapter "):
        try:
            chapter_number = int(grouping.split(":", 1)[0].split()[1])
        except (IndexError, ValueError):
            return "Unmapped chapter questions"
        return CHAPTER_DOMAINS.get(chapter_number, "Unmapped chapter questions")
    return "Unmapped questions"


def chapter_sort_key(chapter: str) -> tuple[int, str]:
    """Sort chapter labels numerically instead of alphabetically."""
    try:
        chapter_number = int(chapter.split(":", 1)[0].split()[1])
    except (IndexError, ValueError):
        chapter_number = sys.maxsize
    return chapter_number, chapter


def short_domain(domain: str) -> str:
    return domain.split(":", 1)[0]


def prompt_choice(prompt: str, valid: set[str]) -> str:
    """Prompt until the user enters one of the allowed case-insensitive values."""
    while True:
        try:
            response = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to the menu.")
            return "q"
        if response in valid:
            return response
        print(f"Please enter one of: {', '.join(value.upper() for value in sorted(valid))}")


def prompt_number(prompt: str, minimum: int, maximum: int, default: int) -> int:
    while True:
        try:
            response = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return default
        if not response:
            return default
        if response.isdigit() and minimum <= int(response) <= maximum:
            return int(response)
        print(f"Enter a number from {minimum} to {maximum}.")


def shuffled_choices(
    question: dict[str, Any], shuffle_answers: bool
) -> tuple[list[tuple[str, str]], str]:
    """Return display choices and the display letter of the correct choice."""
    original_choices = list(question["choices"].items())
    if shuffle_answers:
        random.shuffle(original_choices)

    display_letters = "abcd"
    displayed: list[tuple[str, str]] = []
    correct_display_letter = ""
    for display_letter, (original_letter, choice_text) in zip(
        display_letters, original_choices
    ):
        displayed.append((display_letter, choice_text))
        if original_letter == question["answer"]:
            correct_display_letter = display_letter
    return displayed, correct_display_letter


def show_explanation(question: dict[str, Any]) -> None:
    print("\nExplanation:")
    print(wrapped(question["explanation"]))
    if question.get("corrected"):
        print("\nSource correction:")
        print(wrapped(question.get("correction_note", "The source wording was corrected.")))


def ask_question(
    question: dict[str, Any],
    number: int,
    total: int,
    *,
    shuffle_answers: bool,
) -> str:
    """Present one question and return correct, incorrect, skipped, or quit."""
    divider = "─" * terminal_width()
    print(f"\n{divider}")
    print(f"Question {number} of {total} | {short_domain(question_domain(question))}")
    print(f"Source: {question['grouping']} · Subject: {question['subject']}")
    print(divider)
    print(wrapped(question["question"]))
    print()

    displayed, correct_letter = shuffled_choices(question, shuffle_answers)
    displayed_choices = dict(displayed)
    for letter, choice_text in displayed:
        print(wrapped(f"{letter.upper()}. {choice_text}", subsequent="   "))

    answer = prompt_choice(
        "\nYour answer [A-D, S to skip, Q to end this session]: ",
        {"a", "b", "c", "d", "s", "q"},
    )
    if answer == "q":
        return "quit"
    if answer == "s":
        print("\nSkipped.")
        print(f"Correct answer: {correct_letter.upper()}. {displayed_choices[correct_letter]}")
        show_explanation(question)
        return "skipped"

    if answer == correct_letter:
        print("\nCorrect!")
        result = "correct"
    else:
        print("\nIncorrect.")
        print(f"Correct answer: {correct_letter.upper()}. {displayed_choices[correct_letter]}")
        result = "incorrect"
    show_explanation(question)
    return result


def record_result(
    progress: dict[str, Any], question_id: str, result: str
) -> None:
    if result not in {"correct", "incorrect", "skipped"}:
        return
    record = progress["questions"].setdefault(
        question_id,
        {"attempts": 0, "correct": 0, "incorrect": 0, "skipped": 0},
    )
    record["attempts"] += 1
    record[result] += 1
    record["last_result"] = result


def group_results(
    questions_by_id: dict[str, dict[str, Any]],
    records: dict[str, dict[str, int]],
    *,
    field: str,
) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = defaultdict(
        lambda: {"attempts": 0, "correct": 0, "incorrect": 0, "skipped": 0}
    )
    for question_id, record in records.items():
        question = questions_by_id.get(question_id)
        if not question:
            continue
        name = question_domain(question) if field == "domain" else str(question[field])
        for metric in ("attempts", "correct", "incorrect", "skipped"):
            grouped[name][metric] += int(record.get(metric, 0))
    return dict(grouped)


def print_group_statistics(grouped: dict[str, dict[str, int]]) -> None:
    if not grouped:
        print("No answered questions yet.")
        return
    for name in sorted(grouped):
        record = grouped[name]
        graded = record["correct"] + record["incorrect"]
        accuracy = (record["correct"] / graded * 100) if graded else 0.0
        print(
            f"{name}\n"
            f"  Accuracy: {accuracy:5.1f}%  "
            f"Correct: {record['correct']}  "
            f"Incorrect: {record['incorrect']}  "
            f"Skipped: {record['skipped']}"
        )


def print_session_summary(
    questions_by_id: dict[str, dict[str, Any]],
    session_records: dict[str, dict[str, int]],
) -> None:
    print("\n" + "=" * terminal_width())
    print("Session summary")
    print("=" * terminal_width())
    total_correct = sum(item["correct"] for item in session_records.values())
    total_incorrect = sum(item["incorrect"] for item in session_records.values())
    total_skipped = sum(item["skipped"] for item in session_records.values())
    graded = total_correct + total_incorrect
    accuracy = total_correct / graded * 100 if graded else 0.0
    print(
        f"Accuracy: {accuracy:.1f}% | Correct: {total_correct} | "
        f"Incorrect: {total_incorrect} | Skipped: {total_skipped}"
    )
    print("\nResults by exam domain:")
    print_group_statistics(
        group_results(questions_by_id, session_records, field="domain")
    )


def run_quiz(
    selected: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
    *,
    random_order: bool,
) -> None:
    if not selected:
        print("\nNo questions match that selection.")
        return

    questions = selected.copy()
    if random_order:
        random.shuffle(questions)

    shuffle_answers = (
        prompt_choice("Randomize answer choices too? [y/N]: ", {"y", "n", ""}) == "y"
    )
    session_records: dict[str, dict[str, int]] = {}
    for number, question in enumerate(questions, start=1):
        result = ask_question(
            question, number, len(questions), shuffle_answers=shuffle_answers
        )
        if result == "quit":
            break
        record_result(progress, question["id"], result)
        record_result(
            {"questions": session_records},
            question["id"],
            result,
        )
        save_progress(progress)
        if number < len(questions):
            next_action = prompt_choice(
                "\nPress Enter for the next question, or Q to end: ", {"", "q"}
            )
            if next_action == "q":
                break
            clear_screen()

    print_session_summary(questions_by_id, session_records)


def choose_from_list(title: str, options: list[str]) -> str | None:
    print(f"\n{title}")
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option}")
    print("0. Return to main menu")
    selection = prompt_number("Selection: ", 0, len(options), 0)
    return None if selection == 0 else options[selection - 1]


def study_all(
    questions: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
) -> None:
    print(
        "\nAll questions will be presented in a new random order. "
        "You can end the session at any time; progress is saved after every question."
    )
    run_quiz(
        questions,
        progress,
        questions_by_id,
        random_order=True,
    )


def study_domain(
    questions: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
) -> None:
    domain = choose_from_list("Select an exam domain:", DOMAIN_NAMES)
    if domain is None:
        return
    selected = [question for question in questions if question_domain(question) == domain]
    run_quiz(selected, progress, questions_by_id, random_order=True)


def study_chapter_or_subject(
    questions: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
) -> None:
    print("\n1. Select a chapter")
    print("2. Select a subject")
    print("0. Return to main menu")
    mode = prompt_choice("Selection: ", {"0", "1", "2", "q"})
    if mode in {"0", "q"}:
        return
    field = "grouping" if mode == "1" else "subject"
    if field == "grouping":
        options = sorted(
            {
                question[field]
                for question in questions
                if question["source_section"] == "Chapter Quizzes"
            },
            key=chapter_sort_key,
        )
        title = "Select a chapter:"
    else:
        options = sorted({question[field] for question in questions})
        title = "Select a subject:"
    selection = choose_from_list(title, options)
    if selection is None:
        return
    selected = [question for question in questions if question[field] == selection]
    run_quiz(selected, progress, questions_by_id, random_order=True)


def review_missed(
    questions: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
) -> None:
    missed_ids = {
        question_id
        for question_id, record in progress["questions"].items()
        if int(record.get("incorrect", 0)) > 0
    }
    missed = [question for question in questions if question["id"] in missed_ids]
    if not missed:
        print("\nYou do not have any previously missed questions yet.")
        return
    run_quiz(missed, progress, questions_by_id, random_order=True)


def practice_quiz(
    questions: list[dict[str, Any]],
    progress: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
) -> None:
    count = prompt_number(
        f"\nHow many questions? [default 20, maximum {len(questions)}]: ",
        1,
        len(questions),
        min(20, len(questions)),
    )
    selected = random.sample(questions, count)
    run_quiz(selected, progress, questions_by_id, random_order=False)


def show_statistics(
    questions_by_id: dict[str, dict[str, Any]], progress: dict[str, Any]
) -> None:
    records = progress["questions"]
    print("\n" + "=" * terminal_width())
    print("Cumulative progress by exam domain")
    print("=" * terminal_width())
    print_group_statistics(group_results(questions_by_id, records, field="domain"))

    subjects = group_results(questions_by_id, records, field="subject")
    attempted_subjects = [
        (name, record)
        for name, record in subjects.items()
        if record["correct"] + record["incorrect"] > 0
    ]
    attempted_subjects.sort(
        key=lambda item: (
            item[1]["correct"]
            / max(1, item[1]["correct"] + item[1]["incorrect"]),
            -(item[1]["correct"] + item[1]["incorrect"]),
            item[0],
        )
    )
    if attempted_subjects:
        print("\nLowest-performing subjects (minimum one graded attempt):")
        for name, record in attempted_subjects[:10]:
            graded = record["correct"] + record["incorrect"]
            accuracy = record["correct"] / graded * 100
            print(f"  {accuracy:5.1f}%  {name} ({graded} graded)")


def calculate_weak_areas(
    questions_by_id: dict[str, dict[str, Any]],
    progress: dict[str, Any],
) -> list[dict[str, Any]]:
    """Group attempted questions by domain and subject, then rank weak areas."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for question_id, record in progress["questions"].items():
        question = questions_by_id.get(question_id)
        if not question:
            continue

        key = (question_domain(question), str(question["subject"]))
        area = grouped.setdefault(
            key,
            {
                "domain": key[0],
                "subject": key[1],
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "skipped": 0,
                "missed_questions": [],
            },
        )
        for metric in ("attempts", "correct", "incorrect", "skipped"):
            area[metric] += int(record.get(metric, 0))
        if int(record.get("incorrect", 0)) > 0:
            area["missed_questions"].append(question)

    weak_areas: list[dict[str, Any]] = []
    for area in grouped.values():
        if area["incorrect"] == 0:
            continue
        graded = area["correct"] + area["incorrect"]
        error_rate = area["incorrect"] / graded if graded else 0.0
        area["graded"] = graded
        area["accuracy"] = 1.0 - error_rate
        area["weakness_score"] = area["incorrect"] * error_rate
        weak_areas.append(area)

    weak_areas.sort(
        key=lambda area: (
            -area["weakness_score"],
            area["accuracy"],
            -area["graded"],
            area["domain"],
            area["subject"],
        )
    )
    return weak_areas


def build_review_guide_sections(
    questions_by_id: dict[str, dict[str, Any]],
    progress: dict[str, Any],
) -> list[str]:
    """Build a personalized guide from concepts in previously missed questions."""
    weak_areas = calculate_weak_areas(questions_by_id, progress)
    if not weak_areas:
        return []

    domain_results = group_results(
        questions_by_id, progress["questions"], field="domain"
    )
    domain_priorities: list[tuple[float, str, dict[str, int]]] = []
    for domain, record in domain_results.items():
        graded = record["correct"] + record["incorrect"]
        if not graded or not record["incorrect"]:
            continue
        error_rate = record["incorrect"] / graded
        score = record["incorrect"] * error_rate
        domain_priorities.append((score, domain, record))
    domain_priorities.sort(key=lambda item: (-item[0], item[1]))

    total_correct = sum(record["correct"] for record in domain_results.values())
    total_incorrect = sum(record["incorrect"] for record in domain_results.values())
    total_graded = total_correct + total_incorrect
    overall_accuracy = total_correct / total_graded * 100 if total_graded else 0.0

    overview = [
        "=" * terminal_width(),
        "SECURITY+ PERSONAL REVIEW GUIDE",
        "=" * terminal_width(),
        (
            f"Based on {total_graded} graded attempts: {total_correct} correct and "
            f"{total_incorrect} incorrect ({overall_accuracy:.1f}% accuracy)."
        ),
        "",
        "Priority domains",
    ]
    for index, (_, domain, record) in enumerate(domain_priorities, start=1):
        graded = record["correct"] + record["incorrect"]
        accuracy = record["correct"] / graded * 100
        overview.append(
            f"{index}. {domain} — {accuracy:.1f}% accuracy "
            f"({record['incorrect']} incorrect)"
        )
    overview.extend(
        [
            "",
            (
                "Focus areas are ranked using both the number of incorrect answers "
                "and the error rate. This keeps repeated misses ahead of isolated "
                "mistakes."
            ),
        ]
    )
    sections = ["\n".join(overview)]

    for index, area in enumerate(weak_areas, start=1):
        accuracy = area["accuracy"] * 100
        lines = [
            "=" * terminal_width(),
            f"FOCUS AREA {index}: {area['subject']}",
            f"Domain: {area['domain']}",
            (
                f"Accuracy: {accuracy:.1f}% "
                f"({area['correct']} correct, {area['incorrect']} incorrect)"
            ),
            "=" * terminal_width(),
            "",
            "Key concepts from missed questions",
        ]

        unique_questions: list[dict[str, Any]] = []
        seen_concepts: set[tuple[str, str]] = set()
        for question in area["missed_questions"]:
            correct_letter = question["answer"]
            correct_choice = question["choices"][correct_letter]
            signature = (str(correct_choice), str(question["explanation"]).strip())
            if signature in seen_concepts:
                continue
            seen_concepts.add(signature)
            unique_questions.append(question)

        for concept_number, question in enumerate(unique_questions, start=1):
            correct_letter = question["answer"]
            correct_choice = question["choices"][correct_letter]
            lines.extend(
                [
                    "",
                    wrapped(
                        f"{concept_number}. Question focus: {question['question']}",
                        subsequent="   ",
                    ),
                    wrapped(
                        f"Correct concept: {correct_choice}",
                        indent="   ",
                        subsequent="   ",
                    ),
                    wrapped(
                        question["explanation"],
                        indent="   ",
                        subsequent="   ",
                    ),
                ]
            )
            if question.get("corrected"):
                lines.append(
                    wrapped(
                        f"Source correction: {question['correction_note']}",
                        indent="   ",
                        subsequent="   ",
                    )
                )

        lines.extend(
            [
                "",
                (
                    "Suggested next step: Use option 3, select a subject, and choose "
                    f"“{area['subject']}” for focused practice."
                ),
            ]
        )
        sections.append("\n".join(lines))

    return sections


def save_review_guide(
    sections: list[str], path: Path = REVIEW_GUIDE_PATH
) -> None:
    """Save the latest review guide as a plain-text file."""
    path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def display_review_guide(sections: list[str]) -> None:
    """Display one review-guide section at a time."""
    clear_screen()
    for index, section in enumerate(sections):
        print(section)
        if index < len(sections) - 1:
            action = prompt_choice(
                "\nPress Enter for the next topic, or Q to return to the menu: ",
                {"", "q"},
            )
            if action == "q":
                clear_screen()
                return
            clear_screen()
        else:
            prompt_choice("\nPress Enter to return to the menu: ", {""})
            clear_screen()


def generate_review_guide(
    questions_by_id: dict[str, dict[str, Any]],
    progress: dict[str, Any],
) -> None:
    """Build a guide and let the user display it, save it, or do both."""
    sections = build_review_guide_sections(questions_by_id, progress)
    if not sections:
        print(
            "\nThere are no missed questions yet. Complete a study session, "
            "then return here after answering at least one question incorrectly."
        )
        return

    print("\nReview guide options")
    print("1. Read the guide in the terminal")
    print("2. Save the guide as review_guide.txt")
    print("3. Read and save the guide")
    print("0. Return to main menu")
    selection = prompt_choice("Selection: ", {"0", "1", "2", "3", "q"})
    if selection in {"0", "q"}:
        return
    if selection in {"2", "3"}:
        save_review_guide(sections)
        print(f"\nReview guide saved to: {REVIEW_GUIDE_PATH}")
    if selection in {"1", "3"}:
        if selection == "3":
            prompt_choice("Press Enter to open the guide: ", {""})
        display_review_guide(sections)


def print_menu(question_count: int) -> None:
    print("\n" + "=" * terminal_width())
    print("Security+ Study Quiz")
    print(f"{question_count} questions available")
    print("=" * terminal_width())
    print("1. Study all questions (random order)")
    print("2. Select an exam domain")
    print("3. Select a chapter or subject")
    print("4. Review previously missed questions")
    print("5. Take a practice quiz")
    print("6. View cumulative statistics")
    print("7. Generate missed-question review guide")
    print("8. Quit")


def main() -> None:
    questions = load_questions()
    progress = load_progress()
    questions_by_id = {question["id"]: question for question in questions}

    while True:
        print_menu(len(questions))
        selection = prompt_choice("Selection: ", set("12345678q"))
        if selection == "1":
            study_all(questions, progress, questions_by_id)
        elif selection == "2":
            study_domain(questions, progress, questions_by_id)
        elif selection == "3":
            study_chapter_or_subject(questions, progress, questions_by_id)
        elif selection == "4":
            review_missed(questions, progress, questions_by_id)
        elif selection == "5":
            practice_quiz(questions, progress, questions_by_id)
        elif selection == "6":
            show_statistics(questions_by_id, progress)
        elif selection == "7":
            generate_review_guide(questions_by_id, progress)
        else:
            print("\nGood luck with your Security+ studies!")
            return


if __name__ == "__main__":
    main()
