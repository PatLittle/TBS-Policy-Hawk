#!/usr/bin/env python3

"""Idempotent quarterly PolicyEvolution entries for automated PIN analysis."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path


def fiscal_quarter(day: date) -> dict:
    if day.month >= 4:
        fiscal_start = day.year
        quarter = ((day.month - 4) // 3) + 1
    else:
        fiscal_start = day.year - 1
        quarter = 4
    quarter_start_month = {1: 4, 2: 7, 3: 10, 4: 1}[quarter]
    quarter_start_year = fiscal_start if quarter < 4 else fiscal_start + 1
    start = date(quarter_start_year, quarter_start_month, 1)
    if quarter == 1:
        end = date(fiscal_start, 6, 30)
    elif quarter == 2:
        end = date(fiscal_start, 9, 30)
    elif quarter == 3:
        end = date(fiscal_start, 12, 31)
    else:
        end = date(fiscal_start + 1, 3, 31)
    fiscal_label = f"{fiscal_start}-{str(fiscal_start + 1)[-2:]}"
    return {"fiscal_label": fiscal_label, "quarter": quarter, "start": start, "end": end}


def _demote_headings(markdown: str) -> str:
    return re.sub(r"^(#{2,5})(?=\s)", lambda match: "#" + match.group(1), markdown, flags=re.MULTILINE)


def _header(period: dict) -> str:
    start = period["start"].isoformat()
    end = period["end"].isoformat()
    return (
        f"# Policy Evolution {period['fiscal_label']} Q{period['quarter']}\n\n"
        f"**Period covered:** {start} to {end}  \n"
        "**Source:** Auto-analysis comments added to TBS-Policy-Hawk issues.\n\n"
        "This file compiles policy-change analysis comments for updates detected during the quarter. "
        "Entries are organized chronologically by the effective/update date in the issue GUID.\n\n"
        f"![Policy activity heatmap](screenshots/tbs_policy_hawk_heatmap_{start}_to_{end}.png)\n\n"
        "---\n"
    )


PIN_BLOCK_PATTERN = re.compile(
    r"<!-- policy-hawk:issue-(\d+):start -->.*?"
    r"<!-- policy-hawk:issue-\1:end -->\n*(?:\n---\n*)?",
    flags=re.DOTALL,
)
DATED_HEADING_PATTERN = re.compile(
    r"^## (\d{4}-\d{2}-\d{2}) — (.+)$",
    flags=re.MULTILINE,
)


def _dated_section_sort_key(block: str) -> tuple[str, str, int]:
    heading = DATED_HEADING_PATTERN.search(block)
    if not heading:
        raise ValueError("Malformed dated PolicyEvolution section.")
    marker = re.search(r"<!-- policy-hawk:issue-(\d+):start -->", block)
    issue_link = re.search(r"^\*\*Issue:\*\* \[#(\d+)\]", block, flags=re.MULTILINE)
    issue_number = int(marker.group(1)) if marker else int(issue_link.group(1)) if issue_link else 2**31
    return heading.group(1), heading.group(2).casefold(), issue_number


def _sort_dated_report_sections(markdown: str) -> str:
    """Sort all dated level-2 entries while keeping their complete bodies intact."""
    headings = list(DATED_HEADING_PATTERN.finditer(markdown))
    if not headings:
        return markdown

    starts = []
    for heading in headings:
        prefix = markdown[:heading.start()]
        marker = re.search(r"<!-- policy-hawk:issue-\d+:start -->\n+$", prefix)
        starts.append(marker.start() if marker else heading.start())

    header = markdown[:starts[0]]
    blocks = [
        markdown[start : starts[index + 1] if index + 1 < len(starts) else len(markdown)]
        for index, start in enumerate(starts)
    ]
    return header + "".join(sorted(blocks, key=_dated_section_sort_key))


def upsert_pin_analysis(
    repo_root: Path | str,
    *,
    issue_number: int,
    repo_full_name: str,
    title: str,
    guid: str,
    detected_date: str,
    family: str,
    identifier: str,
    change_type: str,
    analysis: str,
) -> Path:
    day = date.fromisoformat(detected_date)
    period = fiscal_quarter(day)
    root = Path(repo_root)
    report_path = root / f"PolicyEvolution{period['fiscal_label']}Q{period['quarter']}.md"
    existing = report_path.read_text(encoding="utf-8") if report_path.exists() else _header(period)

    marker_start = f"<!-- policy-hawk:issue-{issue_number}:start -->"
    marker_end = f"<!-- policy-hawk:issue-{issue_number}:end -->"
    section = (
        f"{marker_start}\n"
        f"## {detected_date} — {title}\n\n"
        f"**Issue:** [#{issue_number}](https://github.com/{repo_full_name}/issues/{issue_number})  \n"
        f"**Category:** PIN ({family or 'Unknown'})  \n"
        f"**Notice identifier:** {identifier or 'Not stated'}  \n"
        f"**GUID:** `{guid}`  \n"
        f"**Change type:** pin_{change_type}\n\n"
        f"{_demote_headings(analysis).strip()}\n\n"
        f"{marker_end}\n\n---\n"
    )

    target_pattern = re.compile(
        rf"{re.escape(marker_start)}.*?{re.escape(marker_end)}\n*(?:\n---\n*)?",
        flags=re.DOTALL,
    )
    if target_pattern.search(existing):
        updated = target_pattern.sub(lambda _match: section, existing, count=1)
    else:
        separator = "" if not existing else ("\n" if existing.endswith("\n") else "\n\n")
        updated = existing + separator + section
    updated = _sort_dated_report_sections(updated)
    report_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return report_path
