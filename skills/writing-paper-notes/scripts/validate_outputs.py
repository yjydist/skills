#!/usr/bin/env python3
"""Validate the structural contract of writing-paper-notes output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
HTML_COMMENT_BLOCK_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
QUESTION_RE = re.compile(r"^###\s+(\d+)\.\s+\S[^\n]*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)
H1_RE = re.compile(r"^#\s+\S.*$", re.MULTILINE)
SECTION_NAME_RE = re.compile(r"^(?P<number>\d{2,})\.(?P<slug>[^\s/]+)\.md$")
SELF_CHECK_RE = re.compile(r"<!--\s*self-check:\s*(\d+)\s*-->", re.IGNORECASE)
DETAILS_RE = re.compile(r"<details(?:\s[^>]*)?>.*?</details\s*>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)
CONFIDENCE_LINE_RE = re.compile(
    r"^\s*(?:\*\*[^\n*]+[:：]\*\*\s*)?"
    r"\[\s\]\s*1\s+\[\s\]\s*2\s+\[\s\]\s*3\s+\[\s\]\s*4\s+\[\s\]\s*5\s*$",
    re.MULTILINE,
)
ANSWER_LABEL_RE = re.compile(r"^\s*\*\*[^\n*]+[:：]\*\*\s*$")
GENERATOR_PLACEHOLDER_RE = re.compile(
    r"\[(?:paper-specific question|section-specific reconstruction question|paper title|title|authors|"
    r"venue and year|DOI, arXiv ID, or stable URL|version or access date|"
    r"relative link to notes/00\.abstract\.md|Repeat the same answer and confidence structure|"
    r"A concise answer justified by this section)[^\]]*\]",
    re.IGNORECASE,
)
LEAKAGE_LABEL_RE = re.compile(
    r"^(?:#{1,6}\s+|\*\*)"
    r".*(?:answer key|reference answer|sample answer|expected keywords?|solution|"
    r"参考答案|答案解析|示例答案|预期关键词|提示|解题)"
    r".*$",
    re.IGNORECASE | re.MULTILINE,
)
REPRODUCE_STATUS_RE = re.compile(
    r"<!--\s*reproduce-status:\s*(ready|blocked)\s*-->", re.IGNORECASE
)
REPRODUCE_TARGETS_RE = re.compile(
    r"<!--\s*reproduction-targets\s*-->(.*?)"
    r"<!--\s*/reproduction-targets\s*-->",
    re.IGNORECASE | re.DOTALL,
)
REPRODUCE_TASKS_RE = re.compile(
    r"<!--\s*reproduction-tasks\s*-->(.*?)"
    r"<!--\s*/reproduction-tasks\s*-->",
    re.IGNORECASE | re.DOTALL,
)
REPRODUCE_REQUIRED_REGIONS = {
    "status": re.compile(
        r"<!--\s*reproduction-status\s*-->(.*?)"
        r"<!--\s*/reproduction-status\s*-->",
        re.IGNORECASE | re.DOTALL,
    ),
    "resources": re.compile(
        r"<!--\s*reproduction-resources\s*-->(.*?)"
        r"<!--\s*/reproduction-resources\s*-->",
        re.IGNORECASE | re.DOTALL,
    ),
    "evidence": re.compile(
        r"<!--\s*reproduction-evidence\s*-->(.*?)"
        r"<!--\s*/reproduction-evidence\s*-->",
        re.IGNORECASE | re.DOTALL,
    ),
    "completion": re.compile(
        r"<!--\s*reproduction-completion\s*-->(.*?)"
        r"<!--\s*/reproduction-completion\s*-->",
        re.IGNORECASE | re.DOTALL,
    ),
}
TARGET_ROW_RE = re.compile(r"^\|\s*(T\d{3,})\s*\|", re.MULTILINE)
TASK_MARKER_RE = re.compile(r"<!--\s*task:\s*(R\d{3,})\s*-->", re.IGNORECASE)
TASK_CHECKBOX_RE = re.compile(
    r"^\s*-\s*\[(?P<mark>[^\]])\]\s*\*\*(?P<id>R\d{3,})\s+-\s+\S.*?\*\*\s*$",
    re.MULTILINE,
)
ANY_CHECKBOX_RE = re.compile(r"^\s*-\s*\[[^\]]\]", re.MULTILINE)
BLOCKER_RE = re.compile(
    r"<!--\s*blocker:\s*(B\d{3,})\s+targets:\s*"
    r"(T\d{3,}(?:\s*,\s*T\d{3,})*)\s*-->",
    re.IGNORECASE,
)
COST_ESTIMATE_RE = re.compile(
    r"<!--\s*cost-estimate:\s*(reported|estimated|not-applicable)\s+"
    r"currency:\s*([A-Z]{3})\s+amount:\s*(\d+(?:\.\d+)?)\s*-->",
    re.IGNORECASE,
)
REPRODUCE_PLACEHOLDER_RE = re.compile(
    r"\[(?:paper title|canonical citation|version/date|relative directory used by the commands|"
    r"relative link to notes/00\.abstract\.md|State whether the plan is ready|"
    r"Immutable paper, code, data, model|Atomic task blocks in dependency order|"
    r"Exact directory layout|The commands or deterministic procedure|one-action task title|"
    r"exact command or deterministic manual procedure|existing files, versions, values, or none|"
    r"specific file, directory, log, hash, or decision record|observable pass condition|"
    r"paper/code/data locator supporting the instruction|earlier R-IDs or none|T-IDs or none)"
    r"[^\]]*\]",
    re.IGNORECASE,
)
GENERIC_BRACKETED_PLACEHOLDER_RE = re.compile(
    r"\[(?:TODO|TBD|FIXME|insert|replace|fill(?:\s+in)?|add|write|describe|specify|"
    r"paper-specific|section-specific|exact|relative|one-action|observable)"
    r"(?:\s*:)?[^\]]*\](?!\()",
    re.IGNORECASE,
)

REPRODUCE_TASK_FIELDS = (
    "Action",
    "Run class",
    "Inputs",
    "Produces",
    "Done when",
    "Source",
    "Depends on",
    "Targets",
)
REPRODUCE_RUN_CLASSES = {
    "setup",
    "blocker",
    "smoke",
    "official-full",
    "independent-full",
    "evaluation",
    "archive",
}
REPRODUCE_METADATA_FIELDS = (
    "Paper",
    "Paper version",
    "Plan version",
    "Workspace",
    "Notes",
)
ISO_4217_CODES = set(
    """
    AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB
    BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE CHF CHW CLF CLP CNY COP COU CRC CUC
    CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF
    GTQ GYD HKD HNL HRK HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR
    KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP
    MRU MUR MVR MWK MXN MXV MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP
    PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD
    SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD USN UYI
    UYU UYW UZS VED VES VND VUV WST XAF XAG XAU XBA XBB XBC XBD XCD XDR XOF
    XPD XPF XPT XSU XTS XUA XXX YER ZAR ZMW ZWL
    """.split()
)

RESPONSE_MARKER = "response: blank"
CONFIDENCE_MARKER = "confidence: blank"
SINGLETON_BLANK_MARKERS = {
    "reconstruction: blank",
    "revisit-question-numbers: blank",
    "gap-analysis: blank",
    "corrected-understanding: blank",
}
ALLOWED_CARD_COMMENTS = {
    RESPONSE_MARKER,
    CONFIDENCE_MARKER,
    *SINGLETON_BLANK_MARKERS,
}


def _mask_non_link_regions(text: str) -> str:
    """Remove regions where LaTeX or code brackets must not become Markdown links."""

    patterns = (
        r"```.*?```",
        r"~~~.*?~~~",
        r"`+[^`\n]*`+",
        r"<!--.*?-->",
        r"\\\[.*?\\\]",
        r"\\\(.*?\\\)",
        r"(?<!\\)\$\$.*?(?<!\\)\$\$",
        r"(?<!\\)\$(?:\\.|[^$\n])*?(?<!\\)\$",
    )
    masked = text
    for pattern in patterns:
        masked = re.sub(pattern, "", masked, flags=re.DOTALL)
    return masked


def _visible_reproduction_text(text: str, preserve_task_markers: bool = False) -> str:
    """Remove hidden and example-only Markdown while retaining selected machine markers."""

    visible = FENCED_CODE_BLOCK_RE.sub("", text)

    def replace_comment(match: re.Match[str]) -> str:
        comment = match.group(0)
        if preserve_task_markers and (
            TASK_MARKER_RE.fullmatch(comment) or BLOCKER_RE.fullmatch(comment)
        ):
            return comment
        return ""

    return HTML_COMMENT_BLOCK_RE.sub(replace_comment, visible)


def _link_target(raw_target: str) -> str:
    raw_target = raw_target.strip()
    if raw_target.startswith("<") and ">" in raw_target:
        return raw_target[1 : raw_target.index(">")]
    return raw_target.split(maxsplit=1)[0] if raw_target else ""


def markdown_link_targets(path: Path) -> list[str]:
    text = _mask_non_link_regions(path.read_text(encoding="utf-8"))
    return [_link_target(match.group(2)) for match in MARKDOWN_LINK_RE.finditer(text)]


def relative_link_errors(path: Path, output_root: Path) -> list[str]:
    errors: list[str] = []
    for raw_target in markdown_link_targets(path):
        if not raw_target or raw_target.startswith("#"):
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_target):
            continue
        target_path = unquote(raw_target.split("#", 1)[0])
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(output_root.resolve())
        except ValueError:
            errors.append(f"{path}: relative link escapes output root: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"{path}: broken relative link: {raw_target}")
    return errors


def resolved_markdown_links(path: Path) -> set[Path]:
    links: set[Path] = set()
    for raw_target in markdown_link_targets(path):
        if (
            not raw_target
            or raw_target.startswith("#")
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_target)
        ):
            continue
        target_path = unquote(raw_target.split("#", 1)[0])
        if target_path:
            links.add((path.parent / target_path).resolve())
    return links


def _question_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(QUESTION_RE.finditer(text))
    h2_starts = [match.start() for match in H2_RE.finditer(text)]
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        candidates = [start for start in h2_starts if start > match.end()]
        if index + 1 < len(matches):
            candidates.append(matches[index + 1].start())
        end = min(candidates) if candidates else len(text)
        blocks.append((int(match.group(1)), text[match.end() : end]))
    return blocks


def _validate_card(card: Path) -> list[str]:
    errors: list[str] = []
    text = card.read_text(encoding="utf-8")
    blocks = _question_blocks(text)
    numbers = [number for number, _ in blocks]

    if not 8 <= len(numbers) <= 12:
        errors.append(f"SUMMARY.CARD.md has {len(numbers)} numbered questions; expected 8-12")
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"SUMMARY.CARD.md question numbering is not consecutive: {numbers}")

    normalized_comments = [comment.strip() for comment in COMMENT_RE.findall(text)]
    unexpected_comments = sorted(set(normalized_comments) - ALLOWED_CARD_COMMENTS)
    if unexpected_comments:
        errors.append(
            "SUMMARY.CARD.md contains unsupported or potentially answer-bearing HTML comments: "
            + ", ".join(repr(comment) for comment in unexpected_comments)
        )
    for marker in SINGLETON_BLANK_MARKERS:
        count = normalized_comments.count(marker)
        if count != 1:
            errors.append(f"SUMMARY.CARD.md must contain exactly one '<!-- {marker} -->' marker; found {count}")
    if normalized_comments.count(RESPONSE_MARKER) != len(numbers):
        errors.append("SUMMARY.CARD.md must contain one blank response marker per numbered question")
    if normalized_comments.count(CONFIDENCE_MARKER) != len(numbers):
        errors.append("SUMMARY.CARD.md must contain one blank confidence marker per numbered question")

    for number, block in blocks:
        response_token = f"<!-- {RESPONSE_MARKER} -->"
        confidence_token = f"<!-- {CONFIDENCE_MARKER} -->"
        if block.count(response_token) != 1 or block.count(confidence_token) != 1:
            errors.append(f"SUMMARY.CARD.md question {number} is missing its exact blank-field markers")
            continue
        response_start = block.index(response_token)
        confidence_start = block.index(confidence_token)
        if confidence_start < response_start:
            errors.append(f"SUMMARY.CARD.md question {number} has blank-field markers out of order")
            continue

        before_response = block[:response_start]
        between_markers = block[response_start + len(response_token) : confidence_start]
        after_confidence = block[confidence_start + len(confidence_token) :]
        if not ANSWER_LABEL_RE.fullmatch(before_response):
            errors.append(
                f"SUMMARY.CARD.md question {number} has content in the answer field before its blank marker"
            )
        confidence_lines = CONFIDENCE_LINE_RE.findall(between_markers)
        residue = CONFIDENCE_LINE_RE.sub("", between_markers)
        if len(confidence_lines) != 1 or residue.strip():
            errors.append(
                f"SUMMARY.CARD.md question {number} has a prefilled answer or malformed confidence field"
            )
        if after_confidence.strip():
            errors.append(f"SUMMARY.CARD.md question {number} contains content after its confidence marker")

    for marker in SINGLETON_BLANK_MARKERS:
        token = f"<!-- {marker} -->"
        if text.count(token) != 1:
            continue
        marker_end = text.index(token) + len(token)
        next_heading = re.search(r"^#{2,3}\s+\S.*$", text[marker_end:], re.MULTILINE)
        tail_end = marker_end + next_heading.start() if next_heading else len(text)
        if text[marker_end:tail_end].strip():
            errors.append(f"SUMMARY.CARD.md field after '<!-- {marker} -->' is not blank")

    post_check_start = text.find("<!-- corrected-understanding: blank -->")
    if post_check_start >= 0:
        review_field_lines = re.findall(
            r"^-\s+\*\*[^*\n]+[:：]\*\*(.*)$", text[post_check_start:], re.MULTILINE
        )
        if len(review_field_lines) != 3 or any(value.strip() for value in review_field_lines):
            errors.append("SUMMARY.CARD.md next-review fields must be present and blank")

    if re.search(r"\[[xX✓]\]", text):
        errors.append("SUMMARY.CARD.md contains a preselected checkbox")
    if "<details" in text.lower():
        errors.append("SUMMARY.CARD.md must not contain collapsed or hidden answers")
    if LEAKAGE_LABEL_RE.search(text):
        errors.append("SUMMARY.CARD.md appears to contain an answer, hint, or keyword section")
    if GENERATOR_PLACEHOLDER_RE.search(text):
        errors.append("SUMMARY.CARD.md contains an unreplaced generator placeholder")

    return errors


def _validate_section_self_checks(section: Path) -> list[str]:
    errors: list[str] = []
    text = section.read_text(encoding="utf-8")
    marker_matches = list(SELF_CHECK_RE.finditer(text))
    numbers = [int(match.group(1)) for match in marker_matches]

    if len(marker_matches) < 2:
        errors.append(f"{section}: found {len(marker_matches)} self-check markers; expected at least 2")
        return errors
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"{section}: self-check numbering is not consecutive: {numbers}")

    details_blocks = DETAILS_RE.findall(text)
    opening_count = len(re.findall(r"<details(?:\s|>)", text, re.IGNORECASE))
    closing_count = len(re.findall(r"</details\s*>", text, re.IGNORECASE))
    if opening_count != len(marker_matches) or closing_count != len(marker_matches):
        errors.append(
            f"{section}: expected exactly one complete <details> block per self-check; "
            f"found {opening_count} openings and {closing_count} closings for {len(marker_matches)} questions"
        )
    if len(details_blocks) != len(marker_matches):
        errors.append(
            f"{section}: found {len(details_blocks)} complete collapsed answers for "
            f"{len(marker_matches)} self-checks"
        )

    for index, marker in enumerate(marker_matches):
        end = marker_matches[index + 1].start() if index + 1 < len(marker_matches) else len(text)
        segment = text[marker.end() : end]
        blocks = DETAILS_RE.findall(segment)
        if len(blocks) != 1:
            errors.append(
                f"{section}: self-check {numbers[index]} must have exactly one adjacent <details> answer"
            )
            continue
        before_details = segment[: segment.lower().find("<details")]
        if not re.search(r"\S", before_details):
            errors.append(f"{section}: self-check {numbers[index]} has no visible question")
        block = blocks[0]
        summaries = re.findall(r"<summary(?:\s[^>]*)?>.*?</summary\s*>", block, re.I | re.S)
        if len(summaries) != 1:
            errors.append(f"{section}: self-check {numbers[index]} must have exactly one <summary>")
        answer = re.sub(r"</?details(?:\s[^>]*)?>", "", block, flags=re.I)
        answer = re.sub(r"<summary(?:\s[^>]*)?>.*?</summary\s*>", "", answer, flags=re.I | re.S)
        if not answer.strip():
            errors.append(f"{section}: self-check {numbers[index]} has an empty collapsed answer")

    if GENERATOR_PLACEHOLDER_RE.search(text):
        errors.append(f"{section}: contains an unreplaced generator placeholder")
    return errors


def _consecutive_ids(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{index:03d}" for index in range(1, count + 1)]


def _field_value(block: str, field: str) -> str | None:
    matches = re.findall(
        rf"^\s*-\s+\*\*{re.escape(field)}:\*\*\s+(\S.*)$",
        block,
        re.MULTILINE,
    )
    return matches[0].strip() if len(matches) == 1 else None


def _field_count(block: str, field: str) -> int:
    return len(
        re.findall(
            rf"^\s*-\s+\*\*{re.escape(field)}:\*\*\s+(\S.*)$",
            block,
            re.MULTILINE,
        )
    )


def _id_list(value: str, prefix: str) -> list[str] | None:
    if value.lower() == "none":
        return []
    if not re.fullmatch(
        rf"{re.escape(prefix)}\d{{3,}}(?:\s*,\s*{re.escape(prefix)}\d{{3,}})*",
        value,
        re.IGNORECASE,
    ):
        return None
    ids = [
        item.upper()
        for item in re.findall(
            rf"{re.escape(prefix)}\d{{3,}}",
            value,
            re.IGNORECASE,
        )
    ]
    return ids if len(ids) == len(set(ids)) else None


def _markdown_table_cells(line: str) -> list[str]:
    """Split a pipe table row without treating an escaped pipe as a separator."""

    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells: list[str] = []
    current: list[str] = []
    backslashes = 0
    for char in stripped:
        if char == "|" and backslashes % 2 == 0:
            cells.append("".join(current).strip())
            current = []
            backslashes = 0
            continue
        current.append(char)
        if char == "\\":
            backslashes += 1
        else:
            backslashes = 0
    cells.append("".join(current).strip())
    return cells


def _validate_reproduction_plan(plan: Path) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    text = plan.read_text(encoding="utf-8")
    visible_text = _visible_reproduction_text(text)

    status_matches = REPRODUCE_STATUS_RE.findall(text)
    status = status_matches[0].lower() if len(status_matches) == 1 else None
    if len(status_matches) != 1:
        errors.append(
            f"REPRODUCT.md must contain exactly one ready/blocked status comment; found {len(status_matches)}"
        )

    region_values: dict[str, str] = {}
    region_match_positions: dict[str, int] = {}
    for name, pattern in REPRODUCE_REQUIRED_REGIONS.items():
        matches = list(pattern.finditer(text))
        if (
            len(matches) != 1
            or not _visible_reproduction_text(matches[0].group(1)).strip()
        ):
            errors.append(
                f"REPRODUCT.md must contain one non-empty reproduction-{name} region"
            )
        else:
            region_values[name] = matches[0].group(1)
            region_match_positions[name] = matches[0].start()

    target_region_matches = list(REPRODUCE_TARGETS_RE.finditer(text))
    task_region_matches = list(REPRODUCE_TASKS_RE.finditer(text))
    if len(target_region_matches) == 1:
        region_match_positions["targets"] = target_region_matches[0].start()
    if len(task_region_matches) == 1:
        region_match_positions["tasks"] = task_region_matches[0].start()
    expected_region_order = ("status", "targets", "resources", "tasks", "evidence", "completion")
    if all(name in region_match_positions for name in expected_region_order):
        positions = [region_match_positions[name] for name in expected_region_order]
        if positions != sorted(positions):
            errors.append(
                "REPRODUCT.md machine-readable regions are not in the required document order"
            )

    status_region_start = region_match_positions.get("status", len(text))
    visible_header = _visible_reproduction_text(text[:status_region_start])
    h1_matches = H1_RE.findall(visible_header)
    if len(h1_matches) != 1:
        errors.append(f"REPRODUCT.md must contain exactly one visible H1 heading; found {len(h1_matches)}")
    for field in REPRODUCE_METADATA_FIELDS:
        count = _field_count(visible_header, field)
        value = _field_value(visible_header, field)
        if count != 1 or value is None:
            errors.append(
                f"REPRODUCT.md metadata must contain exactly one non-empty '{field}' field"
            )
        elif field == "Plan version" and not re.fullmatch(r"[1-9]\d*", value):
            errors.append("REPRODUCT.md Plan version must be a positive integer")

    cost_matches = COST_ESTIMATE_RE.findall(text)
    if len(cost_matches) != 1:
        errors.append(
            f"REPRODUCT.md must contain exactly one valid cost-estimate marker; found {len(cost_matches)}"
        )
    else:
        cost_status, cost_currency, cost_amount = cost_matches[0]
        resource_cost_matches = COST_ESTIMATE_RE.findall(region_values.get("resources", ""))
        if len(resource_cost_matches) != 1:
            errors.append(
                "REPRODUCT.md cost-estimate marker must be inside the reproduction-resources region"
            )
        if cost_currency.upper() not in ISO_4217_CODES:
            errors.append(
                f"REPRODUCT.md cost estimate uses an unknown ISO 4217 currency code: {cost_currency}"
            )
        if cost_status.lower() == "not-applicable" and cost_amount != "0.00":
            errors.append(
                "REPRODUCT.md not-applicable cost estimate must use amount 0.00"
            )

    target_sections = REPRODUCE_TARGETS_RE.findall(text)
    visible_target_region = (
        _visible_reproduction_text(target_sections[0]) if len(target_sections) == 1 else ""
    )
    target_ids = TARGET_ROW_RE.findall(visible_target_region)
    if len(target_sections) != 1:
        errors.append(
            "REPRODUCT.md must contain exactly one complete reproduction-targets region"
        )
    if not target_ids:
        errors.append("REPRODUCT.md has no reproduction target rows")
    elif target_ids != _consecutive_ids("T", len(target_ids)):
        errors.append(f"REPRODUCT.md target IDs are not unique and consecutive: {target_ids}")
    if visible_target_region:
        for line in visible_target_region.splitlines():
            if not re.match(r"^\|\s*T\d{3,}\s*\|", line):
                continue
            cells = _markdown_table_cells(line)
            if len(cells) != 5 or any(not cell for cell in cells):
                errors.append(f"REPRODUCT.md has an incomplete target row: {line.strip()}")

    task_sections = REPRODUCE_TASKS_RE.findall(text)
    task_region = (
        _visible_reproduction_text(task_sections[0], preserve_task_markers=True)
        if len(task_sections) == 1
        else ""
    )
    if len(task_sections) != 1:
        errors.append("REPRODUCT.md must contain exactly one complete reproduction-tasks region")

    marker_matches = list(TASK_MARKER_RE.finditer(task_region))
    task_ids = [match.group(1).upper() for match in marker_matches]
    if not task_ids:
        errors.append("REPRODUCT.md has no reproduction tasks")
    elif task_ids != _consecutive_ids("R", len(task_ids)):
        errors.append(f"REPRODUCT.md task IDs are not unique and consecutive: {task_ids}")

    referenced_targets: set[str] = set()
    full_target_coverage: set[str] = set()
    run_classes: list[str] = []
    task_details: dict[str, dict[str, object]] = {}
    for index, marker in enumerate(marker_matches):
        task_id = marker.group(1).upper()
        end = marker_matches[index + 1].start() if index + 1 < len(marker_matches) else len(task_region)
        block = task_region[marker.end() : end]
        checkbox_matches = list(TASK_CHECKBOX_RE.finditer(block))
        if len(checkbox_matches) != 1 or checkbox_matches[0].group("id").upper() != task_id:
            errors.append(f"REPRODUCT.md task {task_id} must have one matching task checkbox")
        elif checkbox_matches[0].group("mark") != " ":
            errors.append(f"REPRODUCT.md task {task_id} must start unchecked")

        values: dict[str, str] = {}
        for field in REPRODUCE_TASK_FIELDS:
            count = _field_count(block, field)
            value = _field_value(block, field)
            if count != 1 or value is None:
                errors.append(f"REPRODUCT.md task {task_id} is missing a non-empty '{field}' field")
            else:
                values[field] = value

        run_class = values.get("Run class", "").lower()
        if run_class and run_class not in REPRODUCE_RUN_CLASSES:
            errors.append(f"REPRODUCT.md task {task_id} has invalid Run class: {run_class!r}")
        elif run_class:
            run_classes.append(run_class)

        dependencies = values.get("Depends on", "")
        dependency_ids = _id_list(dependencies, "R")
        if dependency_ids is None:
            errors.append(f"REPRODUCT.md task {task_id} has malformed dependencies: {dependencies!r}")
            dependency_ids = []
        valid_prior_ids = set(task_ids[:index])
        invalid_dependencies = sorted(set(dependency_ids) - valid_prior_ids)
        if invalid_dependencies:
            errors.append(
                f"REPRODUCT.md task {task_id} has unknown or non-prior dependencies: "
                + ", ".join(invalid_dependencies)
            )

        targets = values.get("Targets", "")
        target_list = _id_list(targets, "T")
        if target_list is None:
            errors.append(f"REPRODUCT.md task {task_id} has malformed targets: {targets!r}")
            target_list = []
        referenced = set(target_list)
        unknown_targets = sorted(referenced - set(target_ids))
        if unknown_targets:
            errors.append(
                f"REPRODUCT.md task {task_id} references unknown targets: "
                + ", ".join(unknown_targets)
            )
        referenced_targets.update(referenced)
        if run_class in {"official-full", "independent-full", "evaluation"}:
            full_target_coverage.update(referenced)
        task_details[task_id] = {
            "run_class": run_class,
            "dependencies": dependency_ids,
            "targets": referenced,
        }

    uncovered_targets = sorted(set(target_ids) - referenced_targets)
    if uncovered_targets:
        errors.append(
            "REPRODUCT.md targets are not referenced by any task: " + ", ".join(uncovered_targets)
        )
    targets_without_full_check = sorted(set(target_ids) - full_target_coverage)
    if targets_without_full_check:
        errors.append(
            "REPRODUCT.md targets have no full or evaluation task: "
            + ", ".join(targets_without_full_check)
        )
    if "smoke" not in run_classes:
        errors.append("REPRODUCT.md must contain at least one smoke task")
    if not ({"official-full", "independent-full"} & set(run_classes)):
        errors.append("REPRODUCT.md must contain at least one full reproduction task")
    if "official-full" in run_classes and "independent-full" not in run_classes:
        errors.append(
            "REPRODUCT.md contains an official-full task but no independent-full verification task"
        )

    all_task_checkboxes = ANY_CHECKBOX_RE.findall(task_region)
    if len(all_task_checkboxes) != len(marker_matches):
        errors.append(
            "REPRODUCT.md task region must contain exactly one task checkbox per task marker"
        )

    all_visible_marker_text = _visible_reproduction_text(text, preserve_task_markers=True)
    all_blocker_matches = list(BLOCKER_RE.finditer(all_visible_marker_text))
    blocker_matches = list(BLOCKER_RE.finditer(task_region))
    if len(all_blocker_matches) != len(blocker_matches):
        errors.append("REPRODUCT.md blocker markers must appear inside the reproduction-tasks region")
    blocker_ids = [match.group(1).upper() for match in blocker_matches]
    if blocker_ids and blocker_ids != _consecutive_ids("B", len(blocker_ids)):
        errors.append(f"REPRODUCT.md blocker IDs are not unique and consecutive: {blocker_ids}")
    blocker_targets = {
        item.upper()
        for match in blocker_matches
        for item in re.findall(r"T\d{3,}", match.group(2), re.IGNORECASE)
    }
    unknown_blocker_targets = sorted(blocker_targets - set(target_ids))
    if unknown_blocker_targets:
        errors.append(
            "REPRODUCT.md blockers reference unknown targets: "
            + ", ".join(unknown_blocker_targets)
        )
    if status == "ready" and blocker_ids:
        errors.append("REPRODUCT.md is ready but still contains blocker markers")
    if status == "blocked" and not blocker_ids:
        errors.append("REPRODUCT.md is blocked but contains no blocker marker")
    blocker_run_tasks = {
        task_id
        for task_id, details in task_details.items()
        if details["run_class"] == "blocker"
    }
    if status == "ready" and blocker_run_tasks:
        errors.append("REPRODUCT.md is ready but still contains blocker run-class tasks")

    blocker_task_by_id: dict[str, str] = {}
    blocker_tasks_by_target: dict[str, set[str]] = {}
    for blocker in blocker_matches:
        blocker_id = blocker.group(1).upper()
        following_markers = [marker for marker in marker_matches if marker.start() > blocker.end()]
        if not following_markers:
            errors.append(
                f"REPRODUCT.md blocker {blocker_id} is not immediately followed by a resolution task"
            )
            continue
        resolution_marker = following_markers[0]
        between = task_region[blocker.end() : resolution_marker.start()]
        if between.strip():
            errors.append(
                f"REPRODUCT.md blocker {blocker_id} is not immediately followed by a resolution task"
            )
            continue
        resolution_task = resolution_marker.group(1).upper()
        blocker_task_by_id[blocker_id] = resolution_task
        if task_details.get(resolution_task, {}).get("run_class") != "blocker":
            errors.append(
                f"REPRODUCT.md blocker {blocker_id} resolution task {resolution_task} "
                "must use Run class 'blocker'"
            )
        for target in re.findall(r"T\d{3,}", blocker.group(2), re.IGNORECASE):
            blocker_tasks_by_target.setdefault(target.upper(), set()).add(resolution_task)

    orphan_blocker_tasks = sorted(blocker_run_tasks - set(blocker_task_by_id.values()))
    if orphan_blocker_tasks:
        errors.append(
            "REPRODUCT.md blocker run-class tasks have no immediately preceding blocker marker: "
            + ", ".join(orphan_blocker_tasks)
        )

    dependency_closure: dict[str, set[str]] = {}
    for task_id in task_ids:
        direct = set(task_details.get(task_id, {}).get("dependencies", []))
        dependency_closure[task_id] = direct | {
            ancestor
            for dependency in direct
            for ancestor in dependency_closure.get(dependency, set())
        }

    for task_id, details in task_details.items():
        if details["run_class"] not in {"official-full", "independent-full", "evaluation"}:
            continue
        required_blocker_tasks = {
            blocker_task
            for target in details["targets"]
            for blocker_task in blocker_tasks_by_target.get(target, set())
        }
        missing_gates = sorted(required_blocker_tasks - dependency_closure.get(task_id, set()))
        if missing_gates:
            errors.append(
                f"REPRODUCT.md task {task_id} bypasses blocker resolution tasks: "
                + ", ".join(missing_gates)
            )

    if REPRODUCE_PLACEHOLDER_RE.search(visible_text):
        errors.append("REPRODUCT.md contains an unreplaced generator placeholder")
    if GENERIC_BRACKETED_PLACEHOLDER_RE.search(visible_text):
        errors.append("REPRODUCT.md contains a generic bracketed placeholder")

    return errors, {
        "reproduction_status": status,
        "reproduction_targets": len(target_ids),
        "reproduction_tasks": len(task_ids),
        "reproduction_blockers": len(blocker_ids),
    }


def validate(output_root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    output_root = output_root.resolve()
    card = output_root / "SUMMARY.CARD.md"
    reproduction_plan = output_root / "REPRODUCT.md"
    notes = output_root / "notes"
    overview = notes / "00.abstract.md"

    if not card.is_file():
        errors.append("Missing SUMMARY.CARD.md in the output root")
    if not reproduction_plan.is_file():
        errors.append("Missing REPRODUCT.md in the output root")
    if not overview.is_file():
        errors.append("Missing notes/00.abstract.md")

    direct_note_files = sorted(path for path in notes.glob("*.md") if path.is_file()) if notes.is_dir() else []
    nested_note_files = (
        sorted(path for path in notes.rglob("*.md") if path.is_file() and path.parent != notes)
        if notes.is_dir()
        else []
    )
    for path in nested_note_files:
        errors.append(f"Markdown note must be directly under notes/: {path}")

    section_files: list[Path] = []
    numbered_sections: list[tuple[int, Path]] = []
    for path in direct_note_files:
        if path.name == "00.abstract.md":
            continue
        match = SECTION_NAME_RE.fullmatch(path.name)
        if not match:
            errors.append(f"Invalid section note filename: {path.name}")
            continue
        numbered_sections.append((int(match.group("number")), path))
    numbered_sections.sort(key=lambda item: item[0])
    section_files = [path for _, path in numbered_sections]

    if not section_files:
        errors.append("No section note files found after notes/00.abstract.md")
    section_numbers = [number for number, _ in numbered_sections]
    if section_numbers and section_numbers != list(range(1, len(section_numbers) + 1)):
        errors.append(f"Section note numbering is not consecutive from 01: {section_numbers}")

    if card.is_file():
        errors.extend(_validate_card(card))
    reproduction_metrics: dict[str, object] = {
        "reproduction_status": None,
        "reproduction_targets": 0,
        "reproduction_tasks": 0,
        "reproduction_blockers": 0,
    }
    if reproduction_plan.is_file():
        reproduction_errors, reproduction_metrics = _validate_reproduction_plan(reproduction_plan)
        errors.extend(reproduction_errors)
    if overview.is_file() and GENERATOR_PLACEHOLDER_RE.search(overview.read_text(encoding="utf-8")):
        errors.append("notes/00.abstract.md contains an unreplaced generator placeholder")

    if overview.is_file():
        overview_links = resolved_markdown_links(overview)
        if card.resolve() not in overview_links:
            errors.append("notes/00.abstract.md does not link to ../SUMMARY.CARD.md")
        if reproduction_plan.resolve() not in overview_links:
            errors.append("notes/00.abstract.md does not link to ../REPRODUCT.md")
        for section in section_files:
            if section.resolve() not in overview_links:
                errors.append(f"notes/00.abstract.md reading map does not link to {section.name}")

    if card.is_file() and overview.resolve() not in resolved_markdown_links(card):
        errors.append("SUMMARY.CARD.md does not link to notes/00.abstract.md")
    if reproduction_plan.is_file() and overview.resolve() not in resolved_markdown_links(reproduction_plan):
        errors.append("REPRODUCT.md does not link to notes/00.abstract.md")

    for section in section_files:
        if overview.resolve() not in resolved_markdown_links(section):
            errors.append(f"{section}: does not link back to 00.abstract.md")
        errors.extend(_validate_section_self_checks(section))

    paths_to_check = (
        ([card] if card.is_file() else [])
        + ([reproduction_plan] if reproduction_plan.is_file() else [])
        + direct_note_files
        + nested_note_files
    )
    for path in paths_to_check:
        errors.extend(relative_link_errors(path, output_root))

    if len(section_files) > 30:
        warnings.append(
            "More than 30 section files were generated; verify that subsections were not split into separate files"
        )

    return {
        "valid": not errors,
        "output_root": str(output_root),
        "note_files": len(direct_note_files) + len(nested_note_files),
        "section_files": len(section_files),
        "errors": errors,
        "warnings": warnings,
        **reproduction_metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    result = validate(args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
