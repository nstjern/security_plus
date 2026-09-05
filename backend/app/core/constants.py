"""Exam taxonomy shared by the question bank and the analytics services."""

from __future__ import annotations

API_VERSION = "0.1.0"

DOMAIN_NAMES: tuple[str, ...] = (
    "Domain 1: General Security Concepts",
    "Domain 2: Threats, Vulnerabilities, and Mitigations",
    "Domain 3: Security Architecture",
    "Domain 4: Security Operations",
    "Domain 5: Security Program Management and Oversight",
)

UNMAPPED_CHAPTER_DOMAIN = "Unmapped chapter questions"
UNMAPPED_DOMAIN = "Unmapped questions"

# Fallback mapping for questions that omit an explicit exam_domain.
CHAPTER_DOMAINS: dict[int, str] = {
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
