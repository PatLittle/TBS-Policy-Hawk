#!/usr/bin/env python3
"""
Build a CSV of TBS policy instruments (full output with all hierarchy paths)
from: https://www.tbs-sct.canada.ca/pol/hierarch-eng.aspx

Output columns:
  - ID
  - URL
  - Name
  - Min Level
  - Hierarchy Paths (all paths, separated by ' || ')
  - Other Names (any alternate names encountered for the same ID)

No third-party dependencies required (stdlib only).
"""

import sys
import re
import html as htmllib
import csv
from pathlib import Path
from collections import defaultdict


def strip_html(text: str) -> str:
    """Remove tags and unescape HTML entities."""
    return htmllib.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def parse_events(page_html: str):
    """
    Tokenize the HTML into ordered events:
      - 'anchor' for policy instrument links
      - 'ul_open' when a nested <ul class="tv-ul"> opens
      - 'ul_close' when a </ul> closes
    """
    anchor_pat = re.compile(
        r'<a[^>]*href="([^"]*doc-eng\.aspx\?id=(\d+)[^"]*)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    ul_open_pat = re.compile(r'<ul[^>]*class="[^"]*tv-ul[^"]*"[^>]*>', re.IGNORECASE)
    ul_close_pat = re.compile(r"</ul\s*>", re.IGNORECASE)

    events = []
    for m in anchor_pat.finditer(page_html):
        events.append(
            {
                "pos": m.start(),
                "type": "anchor",
                "url": m.group(1).strip(),
                "id": m.group(2).strip(),
                "name_html": m.group(3),
            }
        )
    for m in ul_open_pat.finditer(page_html):
        events.append({"pos": m.start(), "type": "ul_open"})
    for m in ul_close_pat.finditer(page_html):
        events.append({"pos": m.start(), "type": "ul_close"})

    events.sort(key=lambda x: x["pos"])
    return events


def extract_rows_with_hierarchy(page_html: str):
    """
    Walk ordered events using a stack to reconstruct breadcrumbs (hierarchy path).
    Returns a list of dict rows with:
      ID, URL, Name, Hierarchy Path, Level
    """
    events = parse_events(page_html)

    stack = []       # ancestor names (top -> bottom)
    rows = []
    last_anchor = None

    for ev in events:
        if ev["type"] == "anchor":
            name = strip_html(ev["name_html"])
            parent_path = " > ".join(stack)
            rows.append(
                {
                    "ID": ev["id"],
                    "URL": ev["url"],
                    "Name": name,
                    "Hierarchy Path": parent_path,
                    "Level": len(stack),
                }
            )
            last_anchor = {"Name": name}

        elif ev["type"] == "ul_open":
            if last_anchor is not None:
                stack.append(last_anchor["Name"])
                last_anchor = None

        elif ev["type"] == "ul_close":
            if stack:
                stack.pop()

    return rows


def build_full_records(rows):
    """
    Filter to main-list anchors (doc-eng.aspx?id=...), normalize URLs to absolute,
    and deduplicate by ID, collecting all names and all hierarchy paths.
    """
    BASE = "https://www.tbs-sct.canada.ca/pol/"

    main = []
    for r in rows:
        url = r["URL"].lstrip("./")
        if url.lower().startswith("doc-eng.aspx?id="):
            r["URL"] = BASE + url
            main.append(r)

    by_id = defaultdict(
        lambda: {
            "URL": None,
            "Name": None,   # first-seen primary
            "Level": None,  # min level across occurrences
            "Names": set(),  # all observed names
            "Paths": set(),  # all observed hierarchy paths
        }
    )

    for r in main:
        d = by_id[r["ID"]]
        d["URL"] = d["URL"] or r["URL"]
        d["Name"] = d["Name"] or r["Name"]
        d["Level"] = min(d["Level"], r["Level"]) if d["Level"] is not None else r["Level"]
        d["Names"].add(r["Name"])
        if r["Hierarchy Path"]:
            d["Paths"].add(r["Hierarchy Path"])

    records = []
    for _id, d in by_id.items():
        all_paths = " || ".join(sorted(d["Paths"])) if d["Paths"] else ""
        all_names = sorted(d["Names"])
        primary = d["Name"]
        others = [n for n in all_names if n != primary]
        records.append(
            {
                "ID": _id,
                "URL": d["URL"],
                "Name": primary,
                "Min Level": d["Level"],
                "Hierarchy Paths": all_paths,
                "Other Names": ", ".join(others),
            }
        )

    # Sort by (Min Level, Name) for readability
    records.sort(key=lambda r: (r["Min Level"], r["Name"]))
    return records


def main(argv=None) -> int:
    """
    Usage:
      python build_tbs_policy_hierarchy.py INPUT_HTML OUTPUT_CSV
    Where:
      - INPUT_HTML  : path to a saved copy of hierarch-eng.aspx HTML
      - OUTPUT_CSV  : path to write the full CSV
    """
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print("Usage: build_tbs_policy_hierarchy.py INPUT_HTML OUTPUT_CSV", file=sys.stderr)
        return 2

    in_html = Path(argv[0])
    out_csv = Path(argv[1])

    text = in_html.read_text(encoding="utf-8", errors="ignore")
    rows = extract_rows_with_hierarchy(text)
    records = build_full_records(rows)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ID",
                "URL",
                "Name",
                "Min Level",
                "Hierarchy Paths",
                "Other Names",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} rows to {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())