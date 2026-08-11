"""Tests for the Security+ terminal quiz."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import quiz


class QuestionBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = quiz.load_questions()

    def test_expected_question_count_and_unique_ids(self):
        self.assertEqual(len(self.questions), 136)
        ids = [question["id"] for question in self.questions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_answer_is_a_valid_choice(self):
        for question in self.questions:
            with self.subTest(question=question["id"]):
                self.assertEqual(set(question["choices"]), set("abcd"))
                self.assertIn(question["answer"], question["choices"])

    def test_every_question_has_original_provenance(self):
        for question in self.questions:
            with self.subTest(question=question["id"]):
                self.assertTrue(question["id"].startswith("clean-"))
                self.assertEqual(
                    question["provenance"],
                    "Original question authored for this project; "
                    "not an official CompTIA item.",
                )
                self.assertFalse(question["corrected"])
                self.assertEqual(question["correction_note"], "")

    def test_domain_bank_counts(self):
        counts = {
            domain: sum(
                question["exam_domain"] == domain for question in self.questions
            )
            for domain in quiz.DOMAIN_NAMES
        }
        self.assertEqual(
            counts,
            {
                quiz.DOMAIN_NAMES[0]: 16,
                quiz.DOMAIN_NAMES[1]: 30,
                quiz.DOMAIN_NAMES[2]: 24,
                quiz.DOMAIN_NAMES[3]: 38,
                quiz.DOMAIN_NAMES[4]: 28,
            },
        )

    def test_chapter_counts_and_sequence(self):
        counts = {}
        for question in self.questions:
            counts[question["grouping"]] = counts.get(question["grouping"], 0) + 1
        ordered = sorted(counts, key=quiz.chapter_sort_key)
        self.assertEqual(
            [quiz.chapter_sort_key(chapter)[0] for chapter in ordered],
            list(range(1, 18)),
        )
        self.assertEqual(sum(counts.values()), 136)


class QuizLogicTests(unittest.TestCase):
    def setUp(self):
        self.questions = quiz.load_questions()
        self.questions_by_id = {
            question["id"]: question for question in self.questions
        }

    def test_chapter_and_domain_questions_map_to_domains(self):
        chapter = self.questions_by_id["clean-d04-q033"]
        domain = self.questions_by_id["clean-d02-q002"]
        self.assertEqual(quiz.question_domain(chapter), quiz.DOMAIN_NAMES[3])
        self.assertEqual(quiz.question_domain(domain), quiz.DOMAIN_NAMES[1])

    def test_chapters_sort_in_numeric_order(self):
        chapters = {
            question["grouping"]
            for question in self.questions
            if question["source_section"] == "Chapter Quizzes"
        }
        ordered = sorted(chapters, key=quiz.chapter_sort_key)
        self.assertEqual(
            [quiz.chapter_sort_key(chapter)[0] for chapter in ordered],
            list(range(1, 18)),
        )

    def test_shuffling_choices_preserves_correct_answer(self):
        question = self.questions_by_id["clean-d01-q001"]
        with patch("quiz.random.shuffle", side_effect=lambda values: values.reverse()):
            displayed, answer = quiz.shuffled_choices(question, True)
        displayed_choices = dict(displayed)
        self.assertEqual(
            displayed_choices[answer],
            question["choices"][question["answer"]],
        )

    def test_record_result_accumulates(self):
        progress = quiz.empty_progress()
        quiz.record_result(progress, "sample", "incorrect")
        quiz.record_result(progress, "sample", "correct")
        record = progress["questions"]["sample"]
        self.assertEqual(record["attempts"], 2)
        self.assertEqual(record["correct"], 1)
        self.assertEqual(record["incorrect"], 1)
        self.assertEqual(record["last_result"], "correct")

    def test_progress_round_trip(self):
        progress = quiz.empty_progress()
        quiz.record_result(progress, "sample", "correct")
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "progress.json"
            quiz.save_progress(progress, path)
            self.assertEqual(quiz.load_progress(path), progress)

    def test_group_results_by_domain(self):
        progress = quiz.empty_progress()
        quiz.record_result(progress, "clean-d01-q003", "correct")
        quiz.record_result(progress, "clean-d01-q004", "incorrect")
        grouped = quiz.group_results(
            self.questions_by_id,
            progress["questions"],
            field="domain",
        )
        self.assertEqual(grouped[quiz.DOMAIN_NAMES[0]]["attempts"], 2)
        self.assertEqual(grouped[quiz.DOMAIN_NAMES[0]]["correct"], 1)

    def test_weak_areas_use_error_count_and_rate(self):
        progress = quiz.empty_progress()
        progress["questions"] = {
            "clean-d01-q003": {
                "attempts": 4,
                "correct": 1,
                "incorrect": 3,
                "skipped": 0,
            },
            "clean-d01-q004": {
                "attempts": 1,
                "correct": 0,
                "incorrect": 1,
                "skipped": 0,
            },
        }
        areas = quiz.calculate_weak_areas(self.questions_by_id, progress)
        self.assertEqual(areas[0]["incorrect"], 3)
        self.assertEqual(areas[0]["accuracy"], 0.25)
        self.assertGreater(areas[0]["weakness_score"], areas[1]["weakness_score"])

    def test_review_guide_uses_original_explanations(self):
        progress = quiz.empty_progress()
        question = self.questions_by_id["clean-d03-q001"]
        quiz.record_result(progress, question["id"], "incorrect")
        sections = quiz.build_review_guide_sections(
            self.questions_by_id,
            progress,
        )
        guide = "\n".join(sections)
        normalized_guide = " ".join(guide.split())
        self.assertGreaterEqual(len(sections), 2)
        self.assertIn("SECURITY+ PERSONAL REVIEW GUIDE", guide)
        self.assertIn(
            "A DMZ isolates the internet-facing server",
            normalized_guide,
        )
        self.assertNotIn("Source correction:", guide)

    def test_review_guide_requires_a_missed_question(self):
        progress = quiz.empty_progress()
        quiz.record_result(progress, "clean-d01-q003", "correct")
        self.assertEqual(
            quiz.build_review_guide_sections(self.questions_by_id, progress),
            [],
        )

    def test_review_guide_can_be_saved(self):
        sections = ["Overview", "Focus area"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "review_guide.txt"
            quiz.save_review_guide(sections, path)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "Overview\n\nFocus area\n",
            )

    @patch("quiz.print_session_summary")
    @patch("quiz.save_progress")
    @patch("quiz.clear_screen")
    @patch("quiz.ask_question", side_effect=["correct", "correct"])
    @patch("quiz.prompt_choice", side_effect=["n", ""])
    def test_screen_clears_after_advancing_to_next_question(
        self,
        _prompt_choice,
        _ask_question,
        clear_screen,
        _save_progress,
        _summary,
    ):
        selected = self.questions[:2]
        quiz.run_quiz(
            selected,
            quiz.empty_progress(),
            self.questions_by_id,
            random_order=False,
        )
        clear_screen.assert_called_once_with()

    def test_question_bank_is_utf8_json(self):
        with quiz.QUESTIONS_PATH.open(encoding="utf-8") as question_file:
            parsed = json.load(question_file)
        self.assertEqual(len(parsed), 136)


if __name__ == "__main__":
    unittest.main()
