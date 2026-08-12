# Security+ Study Quiz

A Python 3 terminal quiz with 136 independently authored practice questions
covering the five CompTIA Security+ SY0-701 exam domains.

This project is not affiliated with or endorsed by CompTIA. Its questions are
original study material, not official exam items.

The project is being rebuilt as a full-stack web application. The terminal
program below still works and is unchanged; the API in `backend/` reuses its
domain logic so both rank weaknesses identically.

| Path | What it is |
|---|---|
| `quiz.py`, `test_quiz.py` | The original terminal program |
| `questions.json` | The question bank, shared by both interfaces |
| `backend/` | FastAPI service — see [backend/README.md](backend/README.md) |
| `contracts/` | Generated API contract and architecture decision records |
| `SECURITY.md` | Security controls, mapped to SY0-701 domains |

Start the web stack with `docker compose up --build`, then open
http://localhost:8000/docs.

## Run

From this folder:

```bash
python3 quiz.py
```

Or from the project root:

```bash
python3 security_plus/quiz.py
```

The program uses only the Python standard library.

## Study modes

1. **Study all questions** presents all questions in a newly randomized order.
2. **Select an exam domain** focuses on one SY0-701 domain.
3. **Select a chapter or subject** focuses on a narrower topic.
4. **Review previously missed questions** revisits anything answered incorrectly.
5. **Take a practice quiz** draws a random sample of a chosen size.
6. **View cumulative statistics** shows accuracy by domain and weakest subjects.
7. **Generate a review guide** ranks weak areas and turns missed-question
   explanations into a personalized concept review.

Every study mode can optionally randomize answer choices. Enter `S` to skip a
question or `Q` to end the current session. Progress is saved after each
question in `progress.json`, which is created on the first answered question.

## Personalized review guide

Option 7 calculates a weakness score using both incorrect-answer count and
error rate, then organizes missed concepts by exam domain and subject. The
guide includes the correct concept, its explanation, and a suggested
focused-study subject.

The guide can be read one topic at a time in the terminal, saved to
`review_guide.txt`, or both. Running option 7 again regenerates the guide from
the latest progress.

## Question bank

Each question includes its exam domain, objective, chapter, subject, answer,
explanation, and an explicit original-content provenance statement. Chapters
1–17 and all five domains can be selected directly from the study menus.

## Reset progress

To start over, exit the program and delete `progress.json`. The clean
question bank in `questions.json` is not modified by studying.

## Test

```bash
python3 -m unittest -v test_quiz.py
```
