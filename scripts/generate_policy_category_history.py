#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from build_policy_currency_quarter import (
    build_snapshot,
    canonical_topics,
)

START_QUARTER = ("2025-26Q4", date(2026, 3, 31))
CATEGORY_ORDER = ["Guidelines", "Directive", "Standard", "Policy", "Guide", "Policy framework"]
COLORS = {
    "Guidelines": "#1267D8",
    "Directive": "#168A50",
    "Standard": "#FCB400",
    "Policy": "#7A56C2",
    "Guide": "#E39B00",
    "Policy framework": "#E22900",
}
START_MARKER = "<!-- policy-hawk:category-history:start -->"
END_MARKER = "<!-- policy-hawk:category-history:end -->"


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def commit_at_or_before(snapshot: date) -> str:
    ref = run_git("rev-list", "-1", f"--before={snapshot.isoformat()}T23:59:59Z", "HEAD")
    if not ref:
        raise RuntimeError(f"No repository commit on or before {snapshot}")
    return ref


def read_at(ref: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True)


def fiscal_quarter(day: date) -> tuple[str, date, date]:
    if day.month >= 4:
        fy = day.year
        q = ((day.month - 4) // 3) + 1
    else:
        fy = day.year - 1
        q = 4
    starts = {1: date(fy, 4, 1), 2: date(fy, 7, 1), 3: date(fy, 10, 1), 4: date(fy + 1, 1, 1)}
    ends = {1: date(fy, 6, 30), 2: date(fy, 9, 30), 3: date(fy, 12, 31), 4: date(fy + 1, 3, 31)}
    return f"{fy}-{str(fy + 1)[-2:]}Q{q}", starts[q], ends[q]


def quarter_sequence(target_label: str, target_snapshot: date):
    quarters = [
        ("2025-26Q4", date(2026, 3, 31)),
        ("2026-27Q1", date(2026, 6, 30)),
        ("2026-27Q2", date(2026, 9, 30)),
        ("2026-27Q3", date(2026, 12, 31)),
        ("2026-27Q4", date(2027, 3, 31)),
    ]
    out = []
    for label, end in quarters:
        if label == target_label:
            out.append((label, target_snapshot))
            break
        out.append((label, end))
    return out


def snapshot_counts(snapshot: date, *, working_tree: bool = False):
    if working_tree:
        items_csv = Path("data/items.csv").read_text(encoding="utf-8-sig")
        hierarchy_csv = Path("data/tbs_policy_hierarchy_full.csv").read_text(encoding="utf-8-sig")
        ref = run_git("rev-parse", "HEAD")
    else:
        ref = commit_at_or_before(snapshot)
        items_csv = read_at(ref, "data/items.csv")
        hierarchy_csv = read_at(ref, "data/tbs_policy_hierarchy_full.csv")

    topics = canonical_topics(hierarchy_csv)
    instruments, _ = build_snapshot(snapshot, topics, items_csv)
    counts = Counter(row.get("category") or "Unknown" for row in instruments.values())
    return ref, instruments, counts


def build_payload(target_label: str, snapshot: date, current: bool):
    rows = []
    for label, snap in quarter_sequence(target_label, snapshot):
        is_target = label == target_label
        ref, instruments, counts = snapshot_counts(
            snap, working_tree=(current and is_target)
        )
        rows.append(
            {
                "quarter": label,
                "snapshot_date": snap.isoformat(),
                "commit": ref,
                "total": len(instruments),
                "categories": {name: counts.get(name, 0) for name in CATEGORY_ORDER},
            }
        )
    return {
        "title": "Policy suite instrument composition",
        "quarter": target_label,
        "snapshot_date": snapshot.isoformat(),
        "population_basis": "canonical policy-instrument universe; unique document ID; active snapshot reconstructed from Policy Hawk history",
        "category_order": CATEGORY_ORDER,
        "snapshots": rows,
    }


def esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_svg(payload: dict) -> str:
    W, H = 1500, 720
    left_x, left_y, left_w, left_h = 55, 155, 620, 500
    right_x, right_y, right_w, right_h = 725, 155, 720, 500
    current = payload["snapshots"][-1]
    cats = payload["category_order"]
    max_count = max(current["categories"].values()) or 1
    max_total = max(row["total"] for row in payload["snapshots"]) or 1

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;fill:#15264A}.title{font-size:34px;font-weight:760}.sub{font-size:14px;fill:#4B5563}.h{font-size:18px;font-weight:720}.label{font-size:14px;font-weight:650}.small{font-size:12px;fill:#4B5563}.num{font-size:13px;font-weight:750}.axis{font-size:11px;fill:#667085}</style>',
        '<rect width="100%" height="100%" fill="#F8F9FB"/>',
        f'<rect x="15" y="15" width="{W-30}" height="{H-30}" rx="18" fill="white" stroke="#DCE3EA"/>',
        '<text x="45" y="62" class="title">Policy suite instrument composition</text>',
        f'<text x="45" y="91" class="sub">Unique active instruments in force · snapshot {esc(payload["snapshot_date"])} · canonical Policy Hawk instrument universe</text>',
        f'<text x="45" y="124" class="sub">Current total: {current["total"]} instruments</text>',
        f'<rect x="{left_x}" y="{left_y}" width="{left_w}" height="{left_h}" rx="12" fill="#FBFCFE" stroke="#DCE3EA"/>',
        f'<rect x="{right_x}" y="{right_y}" width="{right_w}" height="{right_h}" rx="12" fill="#FBFCFE" stroke="#DCE3EA"/>',
        f'<text x="{left_x+22}" y="{left_y+34}" class="h">Current category distribution</text>',
        f'<text x="{right_x+22}" y="{right_y+34}" class="h">Composition over time</text>',
    ]

    bar_x = left_x + 190
    bar_w = left_w - 250
    y = left_y + 82
    for cat in cats:
        val = current["categories"].get(cat, 0)
        width = bar_w * val / max_count
        out += [
            f'<text x="{left_x+22}" y="{y+16}" class="label">{esc(cat)}</text>',
            f'<rect x="{bar_x}" y="{y}" width="{width:.1f}" height="24" rx="4" fill="{COLORS[cat]}"/>',
            f'<text x="{bar_x+width+10:.1f}" y="{y+17}" class="num">{val}</text>',
        ]
        y += 61

    chart_x0 = right_x + 60
    chart_y0 = right_y + 78
    chart_h = right_h - 145
    chart_w = right_w - 105
    for tick in range(0, max_total + 1, 50):
        yy = chart_y0 + chart_h - (tick / max_total * chart_h)
        out += [
            f'<line x1="{chart_x0}" y1="{yy:.1f}" x2="{chart_x0+chart_w}" y2="{yy:.1f}" stroke="#E4E7EC"/>',
            f'<text x="{chart_x0-12}" y="{yy+4:.1f}" class="axis" text-anchor="end">{tick}</text>',
        ]

    snaps = payload["snapshots"]
    slot = chart_w / max(1, len(snaps))
    bw = min(120, slot * 0.58)
    for i, row in enumerate(snaps):
        x = chart_x0 + slot * i + (slot - bw) / 2
        ybottom = chart_y0 + chart_h
        for cat in reversed(cats):
            val = row["categories"].get(cat, 0)
            h = chart_h * val / max_total
            ybottom -= h
            out.append(f'<rect x="{x:.1f}" y="{ybottom:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{COLORS[cat]}"/>')
        out += [
            f'<text x="{x+bw/2:.1f}" y="{chart_y0+chart_h+24}" class="label" text-anchor="middle">{esc(row["quarter"])}</text>',
            f'<text x="{x+bw/2:.1f}" y="{chart_y0+chart_h+43}" class="small" text-anchor="middle">{esc(row["snapshot_date"])}</text>',
            f'<text x="{x+bw/2:.1f}" y="{ybottom-8:.1f}" class="num" text-anchor="middle">{row["total"]}</text>',
        ]

    lx = right_x + 20
    ly = right_y + right_h - 25
    for cat in cats:
        out += [
            f'<rect x="{lx}" y="{ly-11}" width="12" height="12" rx="2" fill="{COLORS[cat]}"/>',
            f'<text x="{lx+18}" y="{ly}" class="small">{esc(cat)}</text>',
        ]
        lx += 106 if cat != "Policy framework" else 0

    out += [
        '<text x="45" y="690" class="small">Source: PatLittle/TBS-Policy-Hawk · data/items.csv · data/tbs_policy_hierarchy_full.csv · repository history</text>',
        '</svg>',
    ]
    return "\n".join(out) + "\n"


def section(payload: dict, image_path: str) -> str:
    current = payload["snapshots"][-1]
    bits = ", ".join(f"**{cat} {current['categories'][cat]}**" for cat in payload["category_order"])
    return f"""{START_MARKER}
## Policy suite instrument composition

This view counts each **unique active policy instrument in force once**, using document ID as the identity key and the instrument's `category` at each reconstructed snapshot. It uses the same canonical Policy Hawk policy-instrument universe as the currency profile and excludes PINs, glossary changes, and non-instrument hierarchy nodes.

![Policy suite instrument composition]({image_path})

As of **{payload['snapshot_date']}**, the suite contains **{current['total']} instruments**: {bits}. The stacked bars show the composition at each quarter-end snapshot available in Policy Hawk; the current quarter uses the latest available snapshot.

{END_MARKER}
"""


def update_report(report: Path, block: str) -> None:
    text = report.read_text(encoding="utf-8")
    if START_MARKER in text and END_MARKER in text:
        before = text.split(START_MARKER, 1)[0]
        after = text.split(END_MARKER, 1)[1]
        text = before + block + after
    else:
        anchor = "<!-- policy-hawk:currency-profile:end -->"
        if anchor in text:
            text = text.replace(anchor, anchor + "\n\n" + block, 1)
        else:
            text += "\n\n" + block
    report.write_text(text, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--quarter")
    p.add_argument("--snapshot", type=date.fromisoformat)
    p.add_argument("--report", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--data-output", type=Path)
    p.add_argument("--current", action="store_true")
    args = p.parse_args()

    if args.current:
        snapshot = date.today()
        quarter, _, _ = fiscal_quarter(snapshot)
        report = Path(f"PolicyEvolution{quarter}.md")
        output = Path(f"screenshots/tbs_policy_hawk_category_history_{quarter}.svg")
        data_output = Path(f"data/policy_categories/{quarter}.json")
        current = True
    else:
        if not all([args.quarter, args.snapshot, args.report, args.output, args.data_output]):
            p.error("fixed-quarter mode requires --quarter --snapshot --report --output --data-output")
        quarter, snapshot, report, output, data_output = (
            args.quarter, args.snapshot, args.report, args.output, args.data_output
        )
        current = False

    payload = build_payload(quarter, snapshot, current=current)
    output.parent.mkdir(parents=True, exist_ok=True)
    data_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_svg(payload), encoding="utf-8")
    data_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    update_report(report, section(payload, output.as_posix()))
    print(f"Wrote {output}, {data_output}, and updated {report}")


if __name__ == "__main__":
    main()
