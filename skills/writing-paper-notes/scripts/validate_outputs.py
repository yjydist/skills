"""Validate the structural contract of writing-paper-notes output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
QUESTION_RE = re.compile(r"^###\s+(\d+)\.\s+\S[^\n]*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)
SECTION_NAME_RE = re.compile(r"^(?P<number>\d{2,})\.(?P<slug>[^\s/]+)\.md$")
SELF_CHECK_RE = re.compile(r"<!--\s*self-check:\s*(\d+)\s*-->", re.IGNORECASE)
DETAILS_RE = re.compile(
    r"<details(?:\s[^>]*)?>.*?</details\s*>", re.IGNORECASE | re.DOTALL
)
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
        errors.append(
            f"SUMMARY.CARD.md has {len(numbers)} numbered questions; expected 8-12"
        )
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append(
            f"SUMMARY.CARD.md question numbering is not consecutive: {numbers}"
        )

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
            errors.append(
                f"SUMMARY.CARD.md must contain exactly one '<!-- {marker} -->' marker; found {count}"
            )
    if normalized_comments.count(RESPONSE_MARKER) != len(numbers):
        errors.append(
            "SUMMARY.CARD.md must contain one blank response marker per numbered question"
        )
    if normalized_comments.count(CONFIDENCE_MARKER) != len(numbers):
        errors.append(
            "SUMMARY.CARD.md must contain one blank confidence marker per numbered question"
        )

    for number, block in blocks:
        response_token = f"<!-- {RESPONSE_MARKER} -->"
        confidence_token = f"<!-- {CONFIDENCE_MARKER} -->"
        if block.count(response_token) != 1 or block.count(confidence_token) != 1:
            errors.append(
                f"SUMMARY.CARD.md question {number} is missing its exact blank-field markers"
            )
            continue
        response_start = block.index(response_token)
        confidence_start = block.index(confidence_token)
        if confidence_start < response_start:
            errors.append(
                f"SUMMARY.CARD.md question {number} has blank-field markers out of order"
            )
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
            errors.append(
                f"SUMMARY.CARD.md question {number} contains content after its confidence marker"
            )

    for marker in SINGLETON_BLANK_MARKERS:
        token = f"<!-- {marker} -->"
        if text.count(token) != 1:
            continue
        marker_end = text.index(token) + len(token)
        next_heading = re.search(r"^#{2,3}\s+\S.*$", text[marker_end:], re.MULTILINE)
        tail_end = marker_end + next_heading.start() if next_heading else len(text)
        if text[marker_end:tail_end].strip():
            errors.append(
                f"SUMMARY.CARD.md field after '<!-- {marker} -->' is not blank"
            )

    post_check_start = text.find("<!-- corrected-understanding: blank -->")
    if post_check_start >= 0:
        review_field_lines = re.findall(
            r"^-\s+\*\*[^*\n]+[:：]\*\*(.*)$", text[post_check_start:], re.MULTILINE
        )
        if len(review_field_lines) != 3 or any(
            value.strip() for value in review_field_lines
        ):
            errors.append(
                "SUMMARY.CARD.md next-review fields must be present and blank"
            )

    if re.search(r"\[[xX✓]\]", text):
        errors.append("SUMMARY.CARD.md contains a preselected checkbox")
    if "<details" in text.lower():
        errors.append("SUMMARY.CARD.md must not contain collapsed or hidden answers")
    if LEAKAGE_LABEL_RE.search(text):
        errors.append(
            "SUMMARY.CARD.md appears to contain an answer, hint, or keyword section"
        )
    if GENERATOR_PLACEHOLDER_RE.search(text):
        errors.append("SUMMARY.CARD.md contains an unreplaced generator placeholder")

    return errors


def _validate_section_self_checks(section: Path) -> list[str]:
    errors: list[str] = []
    text = section.read_text(encoding="utf-8")
    marker_matches = list(SELF_CHECK_RE.finditer(text))
    numbers = [int(match.group(1)) for match in marker_matches]

    if len(marker_matches) < 2:
        errors.append(
            f"{section}: found {len(marker_matches)} self-check markers; expected at least 2"
        )
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
        end = (
            marker_matches[index + 1].start()
            if index + 1 < len(marker_matches)
            else len(text)
        )
        segment = text[marker.end() : end]
        blocks = DETAILS_RE.findall(segment)
        if len(blocks) != 1:
            errors.append(
                f"{section}: self-check {numbers[index]} must have exactly one adjacent <details> answer"
            )
            continue
        before_details = segment[: segment.lower().find("<details")]
        if not re.search(r"\S", before_details):
            errors.append(
                f"{section}: self-check {numbers[index]} has no visible question"
            )
        block = blocks[0]
        summaries = re.findall(
            r"<summary(?:\s[^>]*)?>.*?</summary\s*>", block, re.IGNORECASE | re.DOTALL
        )
        if len(summaries) != 1:
            errors.append(
                f"{section}: self-check {numbers[index]} must have exactly one <summary>"
            )
        answer = re.sub(r"</?details(?:\s[^>]*)?>", "", block, flags=re.IGNORECASE)
        answer = re.sub(
            r"<summary(?:\s[^>]*)?>.*?</summary\s*>",
            "",
            answer,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not answer.strip():
            errors.append(
                f"{section}: self-check {numbers[index]} has an empty collapsed answer"
            )

    if GENERATOR_PLACEHOLDER_RE.search(text):
        errors.append(f"{section}: contains an unreplaced generator placeholder")
    return errors


def validate(output_root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    output_root = output_root.resolve()
    card = output_root / "SUMMARY.CARD.md"
    notes = output_root / "notes"
    overview = notes / "00.abstract.md"

    if not card.is_file():
        errors.append("Missing SUMMARY.CARD.md in the output root")
    if not overview.is_file():
        errors.append("Missing notes/00.abstract.md")

    direct_note_files = (
        sorted(path for path in notes.glob("*.md") if path.is_file())
        if notes.is_dir()
        else []
    )
    nested_note_files = (
        sorted(
            path
            for path in notes.rglob("*.md")
            if path.is_file() and path.parent != notes
        )
        if notes.is_dir()
        else []
    )
    for path in nested_note_files:
        errors.append(f"Markdown note must be directly under notes/: {path}")

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
        errors.append(
            f"Section note numbering is not consecutive from 01: {section_numbers}"
        )

    if card.is_file():
        errors.extend(_validate_card(card))
    if overview.is_file() and GENERATOR_PLACEHOLDER_RE.search(
        overview.read_text(encoding="utf-8")
    ):
        errors.append(
            "notes/00.abstract.md contains an unreplaced generator placeholder"
        )

    if overview.is_file():
        overview_links = resolved_markdown_links(overview)
        if card.resolve() not in overview_links:
            errors.append("notes/00.abstract.md does not link to ../SUMMARY.CARD.md")
        for section in section_files:
            if section.resolve() not in overview_links:
                errors.append(
                    f"notes/00.abstract.md reading map does not link to {section.name}"
                )

    if card.is_file() and overview.resolve() not in resolved_markdown_links(card):
        errors.append("SUMMARY.CARD.md does not link to notes/00.abstract.md")

    for section in section_files:
        if overview.resolve() not in resolved_markdown_links(section):
            errors.append(f"{section}: does not link back to 00.abstract.md")
        errors.extend(_validate_section_self_checks(section))

    paths_to_check = (
        ([card] if card.is_file() else []) + direct_note_files + nested_note_files
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
