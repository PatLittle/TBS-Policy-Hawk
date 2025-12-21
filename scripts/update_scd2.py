#!/usr/bin/env python3

import os
import requests
import xml.etree.ElementTree as ET
import hashlib
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import subprocess

### Configuration
REPO_ROOT = Path(__file__).parent.parent

FEEDS = {
    "en": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=300",
    "fr": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=2&count=300",
}

SCD2_PATH = REPO_ROOT / "data" / "tbs_policy_feed_scd2.csv"
TMP_SNAPSHOT = REPO_ROOT / "data" / "tbs_policy_feed_union_by_guid.csv"

TRACKED_COLS = [
    "title_en", "title_fr",
    "link_en", "link_fr",
    "description_en", "description_fr",
]

### Helpers

def fetch_and_union():
    def parse_rss(url, lang):
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        rows = []

        for item in root.findall(".//item"):
            guid = item.findtext("guid")
            if not guid:
                continue
            rows.append({
                "guid": guid.strip(),
                f"title_{lang}": (item.findtext("title") or "").strip(),
                f"link_{lang}": (item.findtext("link") or "").strip(),
                f"description_{lang}": (item.findtext("description") or "").strip(),
                f"pubDate_{lang}": (item.findtext("pubDate") or "").strip(),
            })
        return pd.DataFrame(rows)

    en = parse_rss(FEEDS["en"], "en")
    fr = parse_rss(FEEDS["fr"], "fr")

    df = en.merge(fr, on="guid", how="outer")
    df["pubDate"] = df["pubDate_en"].where(df["pubDate_en"].astype(bool), df["pubDate_fr"])
    df["pubDate"] = pd.to_datetime(df["pubDate"], errors="coerce")

    df.to_csv(TMP_SNAPSHOT, index=False)
    return df

def hash_row(row):
    parts = []
    for c in TRACKED_COLS:
        v = row.get(c, "")
        if pd.isna(v):
            v = ""
        parts.append(str(v).strip())
    blob = "||".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

def load_scd2():
    if SCD2_PATH.exists():
        df = pd.read_csv(SCD2_PATH, dtype=str, keep_default_na=False)
        df["is_current"] = df["is_current"].astype(str).str.lower().isin(["true", "1", "yes"])
        df["version"] = pd.to_numeric(df["version"], errors="coerce").fillna(0).astype(int)
        return df
    else:
        return pd.DataFrame()

def update_scd2(snap: pd.DataFrame, scd2: pd.DataFrame):
    asof = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    snap["hashdiff"] = snap.apply(hash_row, axis=1)

    # First snapshot write
    if scd2.empty:
        out = snap.copy()
        out["effective_from"] = asof
        out["effective_to"] = ""
        out["is_current"] = True
        out["version"] = 1
        return out[["guid","version","is_current","effective_from","effective_to","hashdiff","pubDate"] + TRACKED_COLS]

    current = scd2[scd2["is_current"] == True].copy()

    # --- Detect changed/unchanged/new
    merged = snap.merge(
        current[["guid", "hashdiff", "version"]],
        on="guid",
        how="left",
        suffixes=("","_current")
    )

    # Close out changed rows
    changed = merged.loc[(merged["version"].notna()) & (merged["hashdiff"] != merged["hashdiff_current"]), "guid"]
    if not changed.empty:
        scd2.loc[(scd2["guid"].isin(changed)) & (scd2["is_current"] == True), ["effective_to","is_current"]] = [asof, False]

    # Insert changed + new
    inserts = merged[(merged["version"].isna()) | (merged["hashdiff"] != merged["hashdiff_current"])].copy()
    if not inserts.empty:
        inserts["version"] = inserts["version"].fillna(0).astype(int) + 1
        inserts["effective_from"] = asof
        inserts["effective_to"] = ""
        inserts["is_current"] = True
        scd_cols = ["guid","version","is_current","effective_from","effective_to","hashdiff","pubDate"] + TRACKED_COLS
        scd2 = pd.concat([scd2, inserts[scd_cols]], ignore_index=True)

    # --- Detect deletions
    # GUIDs in history current but not in snapshot
    missing = set(current["guid"]) - set(snap["guid"])
    if missing:
        scd2.loc[(scd2["guid"].isin(missing)) & (scd2["is_current"] == True), ["effective_to","is_current"]] = [asof, False]

    return scd2.sort_values(["guid","version"])

def write_scd2(df):
    SCD2_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(SCD2_PATH, index=False)

def run_git_push():
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", str(SCD2_PATH), str(TMP_SNAPSHOT)], check=True)
    subprocess.run(["git", "diff", "--staged", "--quiet"], check=False)
    subprocess.run(["git", "commit", "-m", "Update SCD2 history"], check=False)
    subprocess.run(["git", "push"], check=True)

### Main
if __name__ == "__main__":
    snapshot = fetch_and_union()
    scd2 = load_scd2()
    updated = update_scd2(snapshot, scd2)
    write_scd2(updated)
    run_git_push()
