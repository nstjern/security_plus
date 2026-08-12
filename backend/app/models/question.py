"""The question bank's domain model.

Validation that ``quiz.py`` performed with hand-written checks is expressed here as
Pydantic constraints, so a malformed bank fails at load time with a precise message.
"""

from __future__ import annotations

import sys

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.constants import CHAPTER_DOMAINS, UNMAPPED_CHAPTER_DOMAIN, UNMAPPED_DOMAIN


class Question(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    source_section: str
    grouping: str
    objective: str
    subject: str
    question_number: int
    question: str
    choices: dict[str, str]
    answer: str
    explanation: str
    provenance: str
    # Optional so user-authored additions can omit them, matching the CLI's tolerance.
    exam_domain: str = ""
    corrected: bool = False
    correction_note: str = ""

    @model_validator(mode="after")
    def answer_must_identify_a_choice(self) -> Question:
        if self.answer not in self.choices:
            raise ValueError(f"{self.id}: answer {self.answer!r} is not one of its choices")
        return self

    @property
    def correct_choice(self) -> str:
        return self.choices[self.answer]

    @property
    def chapter_number(self) -> int | None:
        """Return the chapter number from a ``Chapter N: Title`` grouping label."""
        if not self.grouping.startswith("Chapter "):
            return None
        try:
            return int(self.grouping.split(":", 1)[0].split()[1])
        except (IndexError, ValueError):
            return None

    @property
    def domain(self) -> str:
        """Resolve the exam domain, falling back to the chapter mapping."""
        if self.exam_domain:
            return self.exam_domain
        if self.grouping.startswith("Domain "):
            return self.grouping
        if self.grouping.startswith("Chapter "):
            chapter = self.chapter_number
            if chapter is None:
                return UNMAPPED_CHAPTER_DOMAIN
            return CHAPTER_DOMAINS.get(chapter, UNMAPPED_CHAPTER_DOMAIN)
        return UNMAPPED_DOMAIN

    @property
    def short_domain(self) -> str:
        return self.domain.split(":", 1)[0]


def chapter_sort_key(chapter: str) -> tuple[int, str]:
    """Sort chapter labels numerically rather than alphabetically."""
    try:
        chapter_number = int(chapter.split(":", 1)[0].split()[1])
    except (IndexError, ValueError):
        chapter_number = sys.maxsize
    return chapter_number, chapter
