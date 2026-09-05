#!/usr/bin/env python3
"""Build deterministic quarter currency-profile input from repository history.

The currency profile uses a consistent canonical policy-instrument universe so
historical quarters remain directly comparable with the current-quarter profile.
Each instrument's version is rolled back to the latest ``data/items.csv`` row
whose publication/effective date is on or before the requested snapshot date.

Some long-standing instruments are not attached to one of the ten requested
reporting roots in the current hierarchy export. ``LEGACY_TOPIC_OVERRIDES`` keeps
those established Policy Hawk classifications explicit and reviewable. Cross-cutting
Foundation Framework document 13616 and transient Build Canada Exchange document
32831 are intentionally excluded from the canonical population.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Mapping, Optional


TOPIC_ORDER = [
    "People management",
    "Government security",
    "Results / Evaluation / Audit",
    "Official languages",
    "Financial management",
    "Service and digital",
    "Transfer payments",
    "ATIP",
    "Investment Management",
    "Communications & Federal Identity",
]

BINS = [
    {"label": "<12 months", "min_years": 0, "max_years": 1},
    {"label": "1–3 yr", "min_years": 1, "max_years": 3},
    {"label": "3–5 yr", "min_years": 3, "max_years": 5},
    {"label": "5–10 yr", "min_years": 5, "max_years": 10},
    {"label": "10+ yr", "min_years": 10, "max_years": None},
]

EVENTS = [
    {"date": "2025-03-04", "label": "PM Carney in Office", "color": "#E22900"},
    {"date": "2025-01-25", "label": "Trump II Presidency", "color": "#E39B00"},
    {"date": "2023-01-01", "display_date": "2023-01", "label": "ChatGPT hits 100M users", "color": "#1267D8"},
    {"date": "2020-03-15", "label": "GC offices close for COVID", "color": "#168A50"},
    {"date": "2018-02-01", "display_date": "2018-02", "label": "1st GC Cloud Framework Contracts Award", "color": "#A06B00"},
    {"date": "2015-11-04", "label": "PM Trudeau in Office", "color": "#7A56C2"},
]

TOPIC_ROOTS = [
    ("Official languages", ("Official Languages, Policy on",)),
    ("Transfer payments", ("Transfer Payments, Policy on",)),
    ("Communications & Federal Identity", ("Communications and Federal Identity, Policy on",)),
    ("ATIP", ("Access to Information, Policy on", "Privacy Protection, Policy on")),
    ("Government security", ("Government Security, Policy on",)),
    ("Service and digital", ("Service and Digital, Policy on",)),
    ("Financial management", ("Financial Management, Policy on",)),
    (
        "Investment Management",
        (
            "Planning and Management of Investments, Policy on the",
            "Green Procurement, Policy on",
        ),
    ),
    (
        "People management",
        (
            "People Management, Policy on",
            "Compensation, Policy Framework for the Management of",
        ),
    ),
    (
        "Results / Evaluation / Audit",
        (
            "Results, Policy on",
            "Internal Audit, Policy on",
            "Risk, Framework for the Management of",
            "Compliance, Framework for the Management of",
            "Governance and Expenditure Management Policy Area",
        ),
    ),
]

# Explicitly classified legacy/supporting instruments that are part of the ten
# reporting suites but do not inherit a requested top-level root in the current
# hierarchy CSV. These classifications preserve the established 185-instrument
# currency-profile population.
LEGACY_TOPIC_OVERRIDES = {
    # People management
    "12563": "People management",
    "12583": "People management",
    "12595": "People management",
    "12601": "People management",
    "12602": "People management",
    "12610": "People management",
    "14219": "People management",
    "15772": "People management",
    "15774": "People management",
    "21104": "People management",
    "22379": "People management",
    "32625": "People management",
    # Government security
    "20008": "Government security",
    "32613": "Government security",
    # Results / Evaluation / Audit
    "30656": "Results / Evaluation / Audit",
    "32574": "Results / Evaluation / Audit",
    # Official languages
    "32788": "Official languages",
    # Financial management
    "24970": "Financial management",
    "26332": "Financial management",
    "26952": "Financial management",
    "26953": "Financial management",
    "26954": "Financial management",
    "32663": "Financial management",
    "32781": "Financial management",
    "32782": "Financial management",
    "32783": "Financial management",
    "32798": "Financial management",
    "32799": "Financial management",
    # Service and digital
    "25748": "Service and digital",
    "25761": "Service and digital",
    "26295": "Service and digital",
    "27907": "Service and digital",
    "32707": "Service and digital",
    "32708": "Service and digital",
    "32787": "Service and digital",
    # Investment management
    "13697": "Investment Management",
    "27807": "Investment Management",
}

EXCLUDED_DOCUMENT_IDS = {
    "13616",  # Foundation Framework for Treasury Board Policies: cross-cutting
    "32831",  # transient Build Canada Exchange page; canonical instrument is 12553
}


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def commit_at_or_before(snapshot: date) -> str:
    ref = run_git("rev-list", "-1", f"--before={snapshot.isoformat()}T23:59:59Z", "HEAD")
    if not ref:
        raise RuntimeError(f"No repository commit exists on or before {snapshot}")
    return ref


def document_id_from_guid(guid: str) -> Optional[str]:
    match = re.match(r"^(\d+)_", guid.strip())
    return match.group(1) if match else None


def parse_pub_date(value: str) -> date:
    value = value.strip()
    if not value:
        raise ValueError("empty pubDate")
    return parsedate_to_datetime(value).date()


def latest_item_versions(items_csv: str, snapshot: date) -> Dict[str, dict]:
    latest: Dict[str, dict] = {}
    for row in csv.DictReader(io.StringIO(items_csv)):
        doc_id = document_id_from_guid(row.get("guid", ""))
        if not doc_id or doc_id in EXCLUDED_DOCUMENT_IDS:
            continue
        try:
            version_date = parse_pub_date(row.get("pubDate", ""))
        except (TypeError, ValueError):
            continue
        if version_date > snapshot:
            continue
        candidate = dict(row)
        candidate["document_id"] = doc_id
        candidate["version_date"] = version_date
        previous = latest.get(doc_id)
        if previous is None or version_date > previous["version_date"]:
            latest[doc_id] = candidate
        elif version_date == previous["version_date"]:
            if (candidate.get("updated_date") or "") > (previous.get("updated_date") or ""):
                latest[doc_id] = candidate
    return latest


def classify_topic(row: Mapping[str, str]) -> Optional[str]:
    searchable = " > ".join(
        value for value in (row.get("Hierarchy Paths", ""), row.get("Name", "")) if value
    )
    for topic, roots in TOPIC_ROOTS:
        if any(root in searchable for root in roots):
            return topic
    return None


def canonical_topics(hierarchy_csv: str) -> Dict[str, str]:
    result: Dict[str, str] = dict(LEGACY_TOPIC_OVERRIDES)
    for row in csv.DictReader(io.StringIO(hierarchy_csv)):
        doc_id = (row.get("ID") or "").strip()
        if not doc_id.isdigit() or doc_id in EXCLUDED_DOCUMENT_IDS:
            continue
        topic = classify_topic(row)
        if topic:
            result[doc_id] = topic
    return result


def years_between(later: date, earlier: date) -> float:
    return (later - earlier).days / 365.25


def bin_index(age: float) -> int:
    for index, bucket in enumerate(BINS):
        lo = float(bucket["min_years"])
        hi = bucket["max_years"]
        if age >= lo and (hi is None or age < float(hi)):
            return index
    raise ValueError(age)


def build_snapshot(snapshot_date: date, topic_by_id: Mapping[str, str], items_csv: str):
    version_by_id = latest_item_versions(items_csv, snapshot_date)
    instruments: Dict[str, dict] = {}
    grouped = defaultdict(list)

    for doc_id, topic in topic_by_id.items():
        version = version_by_id.get(doc_id)
        if version is None:
            continue
        instrument = {
            "id": doc_id,
            "topic": topic,
            "title": version.get("title", ""),
            "category": version.get("category", ""),
            "guid": version.get("guid", ""),
            "version_date": version["version_date"].isoformat(),
        }
        instruments[doc_id] = instrument
        grouped[topic].append(instrument)

    stats: Dict[str, dict] = {}
    for topic in TOPIC_ORDER:
        topic_instruments = grouped.get(topic, [])
        ages = [years_between(snapshot_date, date.fromisoformat(i["version_date"])) for i in topic_instruments]
        bins = [0] * len(BINS)
        for age in ages:
            bins[bin_index(age)] += 1
        stats[topic] = {
            "count": len(topic_instruments),
            "avg_age": round(sum(ages) / len(ages), 3) if ages else 0.0,
            "bins": bins,
        }
    return instruments, stats


def change_counts(baseline: Mapping[str, dict], current: Mapping[str, dict]):
    changes = {topic: {"added": 0, "modified": 0, "deleted": 0} for topic in TOPIC_ORDER}
    for doc_id in sorted(set(baseline) | set(current), key=int):
        before = baseline.get(doc_id)
        after = current.get(doc_id)
        if before is None:
            changes[after["topic"]]["added"] += 1
            continue
        if after is None:
            changes[before["topic"]]["deleted"] += 1
            continue
        if before["topic"] != after["topic"]:
            changes[before["topic"]]["deleted"] += 1
            changes[after["topic"]]["added"] += 1
        elif before["version_date"] != after["version_date"]:
            changes[after["topic"]]["modified"] += 1
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarter", required=True, help="Fiscal quarter label, e.g. 2026-27Q1")
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.end < args.start:
        raise SystemExit("--end must be on or after --start")

    start_ref = commit_at_or_before(args.start)
    end_ref = commit_at_or_before(args.end)
    items_csv = Path("data/items.csv").read_text(encoding="utf-8-sig")
    hierarchy_csv = Path("data/tbs_policy_hierarchy_full.csv").read_text(encoding="utf-8-sig")
    topic_by_id = canonical_topics(hierarchy_csv)

    baseline_instruments, baseline_stats = build_snapshot(args.start, topic_by_id, items_csv)
    current_instruments, current_stats = build_snapshot(args.end, topic_by_id, items_csv)
    changes = change_counts(baseline_instruments, current_instruments)

    topics = [
        {
            "name": topic,
            "changes": changes[topic],
            "baseline": baseline_stats[topic],
            "current": current_stats[topic],
        }
        for topic in TOPIC_ORDER
    ]

    quarter_short = args.quarter.split("Q")[-1]
    payload = {
        "title": "Policy suite currency profile",
        "view_label": f"Fiscal Q{quarter_short} change view",
        "quarter": args.quarter,
        "baseline_date": args.start.isoformat(),
        "current_date": args.end.isoformat(),
        "baseline_commit": start_ref,
        "current_commit": end_ref,
        "population_basis": "canonical 10-topic instrument universe; version state rolled back from data/items.csv",
        "max_age_years": 15,
        "width": 1500,
        "topic_order": TOPIC_ORDER,
        "bins": BINS,
        "events": EVENTS,
        "topics": topics,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Baseline reference commit: {start_ref}")
    print(f"End reference commit:      {end_ref}")
    print(f"Baseline instruments mapped: {len(baseline_instruments)}")
    print(f"Current instruments mapped:  {len(current_instruments)}")
    print("Topic summary:")
    for topic in TOPIC_ORDER:
        b = baseline_stats[topic]
        c = current_stats[topic]
        ch = changes[topic]
        print(
            f"  {topic}: {b['count']} -> {c['count']} "
            f"(+{ch['added']} ~{ch['modified']} -{ch['deleted']}); "
            f"avg {b['avg_age']:.2f} -> {c['avg_age']:.2f}"
        )


if __name__ == "__main__":
    main()
