#!/usr/bin/env python3
"""Regression tests for validate_outputs.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_outputs import validate


CARD_HEADER = """# SUMMARY CARD: Test Paper

## Paper

- **Title:** Test Paper
- **Authors:** A. Author
- **Venue / year:** TestConf 2026
- **Canonical source:** test:paper
- **Paper version studied:** v1
- **Notes:** [overview](notes/00.abstract.md)

## Closed-book reconstruction

"""

CARD_FOOTER = """## Reconstruct the whole paper

**Problem -> assumptions -> method or argument -> evidence -> conclusion -> limits**

<!-- reconstruction: blank -->

## Review after reopening the notes

### Questions to revisit

<!-- revisit-question-numbers: blank -->

### What I had wrong or could not explain

<!-- gap-analysis: blank -->

### Corrected understanding, in my own words

<!-- corrected-understanding: blank -->

### Why the gap happened

- [ ] Missing prerequisite

### Next review

- **What I will revisit:**
- **Question I should be able to answer next time:**
- **Review date:**
"""


def question(number: int) -> str:
    return f"""### {number}. Reconstruct paper-specific idea {number}?

**Your answer:**

<!-- response: blank -->

**Confidence before checking:** [ ] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5
<!-- confidence: blank -->

"""


def section_body(extra: str = "") -> str:
    return f"""# 1. Introduction

[Back to overview](00.abstract.md)

The equation below uses escaped display-math brackets and must not be parsed as a link:

\\[
p(\\theta \\mid x) = \\frac{{p(x \\mid \\theta)p(\\theta)}}{{p(x)}}
\\]

{extra}

<!-- self-check: 1 -->
**Question 1: What role does this section play?**

<details>
<summary>Reveal answer</summary>

It establishes the test argument.

</details>

<!-- self-check: 2 -->
**Question 2: What is the evidence boundary?**

<details>
<summary>Reveal answer</summary>

The toy result is not a universal claim.

</details>
"""


class ValidatorTests(unittest.TestCase):
    def make_output(self, question_count: int = 10, section: str | None = None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        notes = root / "notes"
        notes.mkdir()
        (root / "SUMMARY.CARD.md").write_text(
            CARD_HEADER + "".join(question(i) for i in range(1, question_count + 1)) + CARD_FOOTER,
            encoding="utf-8",
        )
        (notes / "00.abstract.md").write_text(
            "# Overview\n\n[Section 1](01.introduction.md)\n\n[Recall card](../SUMMARY.CARD.md)\n",
            encoding="utf-8",
        )
        (notes / "01.introduction.md").write_text(section or section_body(), encoding="utf-8")
        return root

    def test_valid_output_with_display_math(self) -> None:
        result = validate(self.make_output())
        self.assertTrue(result["valid"], result["errors"])

    def test_broken_link_is_rejected(self) -> None:
        root = self.make_output()
        path = root / "notes" / "01.introduction.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n[Missing](missing.md)\n", encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("broken relative link" in error for error in result["errors"]))

    def test_wrong_card_question_count_is_rejected(self) -> None:
        result = validate(self.make_output(question_count=7))
        self.assertFalse(result["valid"])
        self.assertTrue(any("expected 8-12" in error for error in result["errors"]))

    def test_answer_leakage_is_rejected(self) -> None:
        root = self.make_output()
        card = root / "SUMMARY.CARD.md"
        card.write_text(
            card.read_text(encoding="utf-8") + "\n## Reference answers\n\n1. The leaked answer.\n",
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("answer, hint, or keyword" in error for error in result["errors"]))

    def test_prefilled_answer_field_is_rejected(self) -> None:
        root = self.make_output()
        card = root / "SUMMARY.CARD.md"
        text = card.read_text(encoding="utf-8").replace(
            "**Your answer:**\n\n<!-- response: blank -->",
            "**Your answer:**\n\nA prefilled answer.\n\n<!-- response: blank -->",
            1,
        )
        card.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("content in the answer field" in error for error in result["errors"]))

    def test_prefilled_reflection_field_is_rejected(self) -> None:
        root = self.make_output()
        card = root / "SUMMARY.CARD.md"
        text = card.read_text(encoding="utf-8").replace(
            "<!-- gap-analysis: blank -->",
            "<!-- gap-analysis: blank -->\n\nThe model forgot an assumption.",
        )
        card.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("gap-analysis: blank" in error for error in result["errors"]))

    def test_missing_folded_self_check_is_rejected(self) -> None:
        malformed = section_body().replace("<details>", "", 1).replace("</details>", "", 1)
        result = validate(self.make_output(section=malformed))
        self.assertFalse(result["valid"])
        self.assertTrue(any("one complete <details>" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
