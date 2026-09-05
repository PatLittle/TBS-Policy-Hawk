#!/usr/bin/env python3
"""Create or refresh the narrative synopsis beneath a quarterly currency-profile SVG.

The synopsis is derived deterministically from data/policy_currency/{quarter}.json.
It is intended for the quarter-level section of PolicyEvolution*.md and stays
separate from the dated instrument-by-instrument entries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROFILE_START = "<!-- policy-hawk:currency-profile:start -->"
PROFILE_END = "<!-- policy-hawk:currency-profile:end -->"
SYNOPSIS_START = "<!-- policy-hawk:currency-profile-synopsis:start -->"
SYNOPSIS_END = "<!-- policy-hawk:currency-profile-synopsis:end -->"


def pct(n: int, total: int) -> float:
    return (100.0 * n / total) if total else 0.0


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def serial_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def is_quarter_end(date_text: str) -> bool:
    return date_text[5:] in {"06-30", "09-30", "12-31", "03-31"}


def quarter_label(cfg: dict) -> str:
    if cfg.get("quarter"):
        return str(cfg["quarter"])
    month = int(cfg["baseline_date"][5:7])
    return {4: "Q1", 7: "Q2", 10: "Q3", 1: "Q4"}.get(month, "the quarter")


def stale_share(topic: dict) -> float:
    bins = topic["current"]["bins"]
    total = topic["current"]["count"]
    return pct(sum(bins[3:]), total)


def ten_plus_share(topic: dict) -> float:
    bins = topic["current"]["bins"]
    total = topic["current"]["count"]
    return pct(bins[4], total)


def under_three_share(topic: dict) -> float:
    bins = topic["current"]["bins"]
    total = topic["current"]["count"]
    return pct(sum(bins[:2]), total)


def change_count(topic: dict) -> int:
    c = topic["changes"]
    return int(c.get("added", 0)) + int(c.get("modified", 0)) + int(c.get("deleted", 0))


def build_synopsis(cfg: dict) -> str:
    topics = cfg["topics"]
    total = sum(t["current"]["count"] for t in topics)
    if not total:
        raise ValueError("currency profile contains no current instruments")

    by_count = sorted(topics, key=lambda t: (-t["current"]["count"], t["name"]))
    top3 = by_count[:3]
    top3_total = sum(t["current"]["count"] for t in top3)
    smallest = min(topics, key=lambda t: (t["current"]["count"], t["name"]))

    composition = (
        f"The profile contains **{total} current policy instruments** across the ten reporting topics. "
        f"**{top3[0]['name']}** is the largest area with {top3[0]['current']['count']} instruments "
        f"({fmt_pct(pct(top3[0]['current']['count'], total))} of the suite), followed by "
        f"**{top3[1]['name']}** with {top3[1]['current']['count']} "
        f"({fmt_pct(pct(top3[1]['current']['count'], total))}) and **{top3[2]['name']}** with "
        f"{top3[2]['current']['count']} ({fmt_pct(pct(top3[2]['current']['count'], total))}). "
        f"Together, those three areas account for **{fmt_pct(pct(top3_total, total))}** of current instruments. "
        f"At the other end of the distribution, **{smallest['name']}** contains {smallest['current']['count']} "
        f"instruments ({fmt_pct(pct(smallest['current']['count'], total))})."
    )

    by_age = sorted(topics, key=lambda t: (-t["current"]["avg_age"], t["name"]))
    oldest = by_age[0]
    second_oldest = by_age[1]
    youngest = min(topics, key=lambda t: (t["current"]["avg_age"], t["name"]))
    young_sorted = sorted(topics, key=lambda t: (t["current"]["avg_age"], t["name"]))
    second_youngest = young_sorted[1]

    age_text = (
        f"The age profile differs sharply across topics. **{oldest['name']}** has the oldest current-version "
        f"population, averaging **{oldest['current']['avg_age']:.1f} years**; "
        f"{fmt_pct(stale_share(oldest))} of its instruments are at least five years since their current version, "
        f"including {fmt_pct(ten_plus_share(oldest))} at 10+ years. **{second_oldest['name']}** also has a comparatively "
        f"older profile at **{second_oldest['current']['avg_age']:.1f} years** on average, with "
        f"{fmt_pct(stale_share(second_oldest))} at five years or more. By contrast, **{youngest['name']}** averages "
        f"just **{youngest['current']['avg_age']:.1f} years**, with {fmt_pct(under_three_share(youngest))} of instruments "
        f"revised within the last three years; **{second_youngest['name']}** is also relatively recent at "
        f"**{second_youngest['current']['avg_age']:.1f} years** on average. These are differences in recency of the "
        f"current versions, not assessments of policy quality or effectiveness."
    )

    total_changes = sum(change_count(t) for t in topics)
    change_paragraph = ""
    if total_changes:
        changed = sorted((t for t in topics if change_count(t)), key=lambda t: (-change_count(t), t["name"]))
        leader = changed[0]
        leader_changes = change_count(leader)
        leader_suite_share = pct(leader["current"]["count"], total)
        leader_change_share = pct(leader_changes, total_changes)

        change_breakdown = []
        for t in changed[:3]:
            c = change_count(t)
            change_breakdown.append(
                f"**{t['name']}** {c} ({fmt_pct(pct(c, total_changes))})"
            )

        zero_large = [t for t in by_count if change_count(t) == 0]
        zero_note = ""
        if zero_large:
            z = zero_large[0]
            zero_note = (
                f" **{z['name']}**, despite representing {fmt_pct(pct(z['current']['count'], total))} of the suite, "
                f"recorded no distinct instrument changes in this period."
            )

        c = leader["changes"]
        types = []
        if c.get("added", 0):
            types.append(f"{c['added']} added")
        if c.get("modified", 0):
            types.append(f"{c['modified']} modified")
        if c.get("deleted", 0):
            types.append(f"{c['deleted']} deleted")
        leader_type_text = serial_join(types)

        if is_quarter_end(cfg["current_date"]):
            opening = f"Over {quarter_label(cfg)}, the profile recorded **{total_changes} distinct instrument changes**."
        else:
            opening = f"So far in {quarter_label(cfg)}, the profile records **{total_changes} distinct instrument changes**."

        change_paragraph = (
            opening + " "
            f"The changes are concentrated in {serial_join(change_breakdown)}. "
            f"**{leader['name']}** accounts for **{fmt_pct(leader_change_share)} of all recorded changes** while containing "
            f"only {fmt_pct(leader_suite_share)} of current instruments"
            + (f" ({leader_type_text})" if leader_type_text else "")
            + ", indicating substantially higher change activity than its share of the suite would suggest."
            + zero_note
        )

    parts = ["### Currency profile synopsis", "", composition, "", age_text]
    if change_paragraph:
        parts.extend(["", change_paragraph])
    return "\n".join(parts)


def update_report(report_path: Path, cfg: dict) -> None:
    text = report_path.read_text(encoding="utf-8")
    if PROFILE_START not in text or PROFILE_END not in text:
        raise ValueError(f"{report_path} does not contain a currency-profile section")

    profile_start = text.index(PROFILE_START)
    profile_end = text.index(PROFILE_END, profile_start)
    section = text[profile_start:profile_end]

    synopsis = build_synopsis(cfg)
    wrapped = f"{SYNOPSIS_START}\n{synopsis}\n{SYNOPSIS_END}"

    if SYNOPSIS_START in section and SYNOPSIS_END in section:
        s = section.index(SYNOPSIS_START)
        e = section.index(SYNOPSIS_END, s) + len(SYNOPSIS_END)
        section = section[:s] + wrapped + section[e:]
    else:
        image_pos = section.find("](")
        if image_pos == -1:
            raise ValueError("currency-profile section does not contain an image")
        line_end = section.find("\n", image_pos)
        if line_end == -1:
            line_end = len(section)
        section = section[:line_end] + "\n\n" + wrapped + section[line_end:]

    updated = text[:profile_start] + section + text[profile_end:]
    report_path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    cfg = json.loads(args.input.read_text(encoding="utf-8"))
    update_report(args.report, cfg)


if __name__ == "__main__":
    main()
