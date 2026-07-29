#!/usr/bin/env python3
"""Regression tests for validate_outputs.py."""

from __future__ import annotations

import re
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

REPRODUCE_PLAN = """# REPRODUCE: Test Paper

- **Paper:** Test Paper
- **Paper version:** v1
- **Plan version:** 1
- **Workspace:** reproduce/
- **Notes:** [overview](notes/00.abstract.md)

<!-- reproduce-status: ready -->

## Reproduction status

<!-- reproduction-status -->

Ready for execution.

<!-- /reproduction-status -->

## Definition of done

<!-- reproduction-targets -->

| ID | Central claim and source locator | Result to reproduce | Acceptance rule | Evidence artifact |
|---|---|---|---|---|
| T001 | Claim one, Section 3 | result one | exact match | evidence/t001.json |
| T002 | Claim two, Table 1 | result two | displayed precision | evidence/t002.json |

<!-- /reproduction-targets -->

## Provenance and required resources

<!-- reproduction-resources -->

<!-- cost-estimate: estimated currency: USD amount: 0.25 -->

Use repository commit abc123 and the test fixture checksum 012345.

<!-- /reproduction-resources -->

## Task checklist

<!-- reproduction-tasks -->

<!-- task: R001 -->
- [ ] **R001 - Pin the source fixture**
  - **Action:** Copy fixture.txt to reproduce/input/fixture.txt.
  - **Run class:** setup
  - **Inputs:** fixture.txt at checksum 012345
  - **Produces:** reproduce/input/fixture.txt
  - **Done when:** The copied file has checksum 012345.
  - **Source:** Test Paper, Section 2
  - **Depends on:** none
  - **Targets:** none

<!-- task: R002 -->
- [ ] **R002 - Run the smoke fixture**
  - **Action:** Run python3 official.py --smoke --input reproduce/input/fixture.txt --output evidence/smoke.json.
  - **Run class:** smoke
  - **Inputs:** reproduce/input/fixture.txt and official.py at commit abc123
  - **Produces:** evidence/smoke.json
  - **Done when:** The fixture exits successfully and writes its deterministic sentinel value.
  - **Source:** Test Paper, Section 3
  - **Depends on:** R001
  - **Targets:** none

<!-- task: R003 -->
- [ ] **R003 - Compute result one**
  - **Action:** Run python3 official.py --input reproduce/input/fixture.txt --output evidence/t001.json.
  - **Run class:** official-full
  - **Inputs:** reproduce/input/fixture.txt and official.py at commit abc123
  - **Produces:** evidence/t001.json
  - **Done when:** The result field equals the Section 3 value.
  - **Source:** Test Paper, Section 3
  - **Depends on:** R001, R002
  - **Targets:** T001

<!-- task: R004 -->
- [ ] **R004 - Independently compute result two**
  - **Action:** Run python3 independent.py --input reproduce/input/fixture.txt --output evidence/t002.json.
  - **Run class:** independent-full
  - **Inputs:** reproduce/input/fixture.txt and independent.py
  - **Produces:** evidence/t002.json
  - **Done when:** The result matches Table 1 through displayed precision.
  - **Source:** Test Paper, Table 1
  - **Depends on:** R001, R002
  - **Targets:** T002

<!-- /reproduction-tasks -->

## Evidence package

<!-- reproduction-evidence -->

Preserve the input checksum, environment, commands, logs, and both JSON result files.

<!-- /reproduction-evidence -->

## Completion report

<!-- reproduction-completion -->

Compare each evidence file with its predefined target rule and record pass or fail.

<!-- /reproduction-completion -->
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
        (root / "REPRODUCT.md").write_text(REPRODUCE_PLAN, encoding="utf-8")
        (notes / "00.abstract.md").write_text(
            "# Overview\n\n[Section 1](01.introduction.md)\n\n"
            "[Recall card](../SUMMARY.CARD.md)\n\n[Reproduction plan](../REPRODUCT.md)\n",
            encoding="utf-8",
        )
        (notes / "01.introduction.md").write_text(section or section_body(), encoding="utf-8")
        return root

    def test_valid_output_with_display_math(self) -> None:
        result = validate(self.make_output())
        self.assertTrue(result["valid"], result["errors"])

    def test_hidden_reproduction_target_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        row = "| T001 | Claim one, Section 3 | result one | exact match | evidence/t001.json |"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(row, f"<!--\n{row}\n-->"),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("not unique and consecutive" in error for error in result["errors"]))

    def test_hidden_reproduction_task_body_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = re.sub(
            r"(<!-- task: R001 -->)\n(.*?)(?=\n<!-- task: R002 -->)",
            r"\1\n<!--\n\2\n-->",
            plan.read_text(encoding="utf-8"),
            flags=re.DOTALL,
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("matching task checkbox" in error for error in result["errors"]))

    def test_missing_reproduction_metadata_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace("- **Workspace:** reproduce/\n", ""),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("'Workspace' field" in error for error in result["errors"]))

    def test_generic_bracketed_placeholder_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "Copy fixture.txt to reproduce/input/fixture.txt.",
                "[TODO: insert exact command]",
                1,
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("generic bracketed placeholder" in error for error in result["errors"]))

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

    def test_missing_reproduction_plan_is_rejected(self) -> None:
        root = self.make_output()
        (root / "REPRODUCT.md").unlink()
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing REPRODUCT.md" in error for error in result["errors"]))

    def test_checked_reproduction_task_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace("- [ ] **R001", "- [x] **R001", 1),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("must start unchecked" in error for error in result["errors"]))

    def test_duplicate_reproduction_task_id_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace("<!-- task: R004 -->", "<!-- task: R003 -->")
        text = text.replace("**R004 -", "**R003 -")
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("task IDs are not unique" in error for error in result["errors"]))

    def test_forward_reproduction_dependency_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "- **Depends on:** none", "- **Depends on:** R003", 1
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-prior dependencies" in error for error in result["errors"]))

    def test_uncovered_reproduction_target_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace("- **Targets:** T002", "- **Targets:** none"),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("not referenced by any task" in error for error in result["errors"]))

    def test_blocked_status_requires_a_blocker_marker(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "reproduce-status: ready", "reproduce-status: blocked"
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("contains no blocker marker" in error for error in result["errors"]))

    def test_valid_blocked_reproduction_plan(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace("reproduce-status: ready", "reproduce-status: blocked")
        text = text.replace("<!-- task: R001 -->", "<!-- blocker: B001 targets: T001 -->\n<!-- task: R001 -->")
        text = text.replace("- **Run class:** setup", "- **Run class:** blocker", 1)
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["reproduction_status"], "blocked")
        self.assertEqual(result["reproduction_blockers"], 1)

    def test_reproduction_placeholder_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8") + "\n[Exact directory layout to preserve.]\n",
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("generator placeholder" in error for error in result["errors"]))

    def test_empty_reproduction_evidence_region_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = re.sub(
            r"<!-- reproduction-evidence -->.*?<!-- /reproduction-evidence -->",
            "<!-- reproduction-evidence -->\n\n<!-- /reproduction-evidence -->",
            text,
            flags=re.DOTALL,
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("non-empty reproduction-evidence" in error for error in result["errors"]))

    def test_incomplete_reproduction_target_row_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8").replace(
            "| T001 | Claim one, Section 3 | result one | exact match | evidence/t001.json |",
            "| T001 | Claim one, Section 3 | result one | | evidence/t001.json |",
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("incomplete target row" in error for error in result["errors"]))

    def test_missing_cost_estimate_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = re.sub(r"<!-- cost-estimate:.*?-->", "", plan.read_text(encoding="utf-8"))
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("cost-estimate marker" in error for error in result["errors"]))

    def test_cost_estimate_outside_resource_region_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        marker = "<!-- cost-estimate: estimated currency: USD amount: 0.25 -->"
        text = text.replace(marker, "")
        text = text.replace("## Task checklist", f"{marker}\n\n## Task checklist")
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("inside the reproduction-resources" in error for error in result["errors"]))

    def test_nonzero_not_applicable_cost_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "cost-estimate: estimated currency: USD amount: 0.25",
                "cost-estimate: not-applicable currency: USD amount: 0.25",
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("must use amount 0.00" in error for error in result["errors"]))

    def test_not_applicable_cost_requires_exact_decimal_spelling(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "cost-estimate: estimated currency: USD amount: 0.25",
                "cost-estimate: not-applicable currency: USD amount: 0",
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("must use amount 0.00" in error for error in result["errors"]))

    def test_unknown_currency_code_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace("currency: USD", "currency: ABC"),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown ISO 4217" in error for error in result["errors"]))

    def test_missing_smoke_task_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8").replace(
            "- **Run class:** smoke", "- **Run class:** setup"
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("at least one smoke task" in error for error in result["errors"]))

    def test_invalid_run_class_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8").replace(
            "- **Run class:** setup", "- **Run class:** batch", 1
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("invalid Run class" in error for error in result["errors"]))

    def test_official_full_requires_independent_full(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "- **Run class:** independent-full",
                "- **Run class:** official-full",
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("no independent-full" in error for error in result["errors"]))

    def test_extra_checked_checkbox_in_task_region_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "<!-- /reproduction-tasks -->",
                "- [x] Already completed\n\n<!-- /reproduction-tasks -->",
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("one task checkbox per task marker" in error for error in result["errors"]))

    def test_escaped_pipe_in_target_cell_is_accepted(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "| T001 | Claim one, Section 3 | result one | exact match | evidence/t001.json |",
                "| T001 | Claim one, Section 3 | result A \\| result B | exact match | evidence/t001.json |",
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertTrue(result["valid"], result["errors"])

    def test_smoke_only_target_coverage_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace("- **Run class:** official-full", "- **Run class:** smoke")
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("no full or evaluation task: T001" in error for error in result["errors"]))

    def test_blocker_resolution_task_must_use_blocker_run_class(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace("reproduce-status: ready", "reproduce-status: blocked")
        text = text.replace(
            "<!-- task: R001 -->",
            "<!-- blocker: B001 targets: T001 -->\n<!-- task: R001 -->",
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("must use Run class 'blocker'" in error for error in result["errors"]))

    def test_ready_plan_rejects_orphan_blocker_task(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "- **Run class:** setup", "- **Run class:** blocker", 1
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("ready but still contains blocker run-class" in error for error in result["errors"]))

    def test_full_task_must_depend_on_affected_blocker(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        text = plan.read_text(encoding="utf-8")
        text = text.replace("reproduce-status: ready", "reproduce-status: blocked")
        text = text.replace(
            "<!-- task: R001 -->",
            "<!-- blocker: B001 targets: T001 -->\n<!-- task: R001 -->",
        )
        text = text.replace("- **Run class:** setup", "- **Run class:** blocker", 1)
        text = text.replace(
            "- **Depends on:** R001, R002\n  - **Targets:** T001",
            "- **Depends on:** none\n  - **Targets:** T001",
        )
        plan.write_text(text, encoding="utf-8")
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("bypasses blocker resolution tasks" in error for error in result["errors"]))

    def test_duplicate_required_task_field_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "  - **Inputs:** fixture.txt at checksum 012345",
                "  - **Inputs:** fixture.txt at checksum 012345\n"
                "  - **Inputs:** a conflicting ambient input",
                1,
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing a non-empty 'Inputs' field" in error for error in result["errors"]))

    def test_free_form_dependency_list_is_rejected(self) -> None:
        root = self.make_output()
        plan = root / "REPRODUCT.md"
        plan.write_text(
            plan.read_text(encoding="utf-8").replace(
                "- **Depends on:** R001, R002",
                "- **Depends on:** R001 and R002",
                1,
            ),
            encoding="utf-8",
        )
        result = validate(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("malformed dependencies" in error for error in result["errors"]))

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
