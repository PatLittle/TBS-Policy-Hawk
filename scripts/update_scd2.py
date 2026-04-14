#!/usr/bin/env python3

import os
import re
import requests
import xml.etree.ElementTree as ET
import hashlib
import pandas as pd
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path
import subprocess

### Configuration
REPO_ROOT = Path(__file__).parent.parent

FEEDS = {
    "en": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=300",
    "fr": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=2&count=300",
}
USER_AGENT = os.getenv("TBS_POLICY_HAWK_USER_AGENT", "TBS-Policy-Hawk/1.0 (+https://github.com/TBS-Policy-Hawk)")

FALLBACK_FEEDS = {
    "en": [
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=79",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=27",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=73",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=36",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=83",
    ],
    "fr": [
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=1&type=79",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=1&type=27",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=1&type=73",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=1&type=36",
        "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-fra.aspx?feed=1&type=83",
    ],
}
MODIFICATIONS_TABLE_URLS = {
    "en": "https://www.tbs-sct.canada.ca/pol/modifications-eng.aspx",
    "fr": "https://www.tbs-sct.canada.ca/pol/modifications-fra.aspx",
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
    def normalize_entry(entry, lang):
        guid = entry.get("guid") or entry.get("id") or entry.get("link")
        if not guid:
            return None
        return {
            "guid": guid.strip(),
            f"title_{lang}": (entry.get("title") or "").strip(),
            f"link_{lang}": (entry.get("link") or "").strip(),
            f"description_{lang}": (entry.get("summary") or entry.get("description") or "").strip(),
            f"pubDate_{lang}": (entry.get("published") or "").strip(),
        }

    def parse_feedparser(url, lang):
        try:
            parsed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
        except TypeError:
            parsed = feedparser.parse(url)
        if getattr(parsed, "bozo", False) or not getattr(parsed, "entries", []):
            return None
        rows = [normalize_entry(entry, lang) for entry in parsed.entries]
        rows = [r for r in rows if r is not None]
        return pd.DataFrame(rows)

    def parse_fallback_feeds(lang):
        deduped = {}
        for url in FALLBACK_FEEDS[lang]:
            parsed = parse_feedparser(url, lang)
            if parsed is None or parsed.empty:
                continue
            for row in parsed.to_dict(orient="records"):
                guid = row["guid"]
                existing = deduped.get(guid)
                if not existing:
                    deduped[guid] = row
                    continue

                current_date = pd.to_datetime(row.get(f"pubDate_{lang}", ""), errors="coerce")
                existing_date = pd.to_datetime(existing.get(f"pubDate_{lang}", ""), errors="coerce")
                if pd.notna(current_date) and (pd.isna(existing_date) or current_date > existing_date):
                    deduped[guid] = row

        return pd.DataFrame(deduped.values())

    def parse_rss(url, lang):
        resp = requests.get(url, timeout=60, headers={"User-Agent": USER_AGENT})
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

    def parse_modifications_table(lang):
        url = MODIFICATIONS_TABLE_URLS[lang]
        response = requests.get(url, timeout=60, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="results-table")
        if not table:
            return pd.DataFrame()

        rows = []
        for tr in table.select("tbody tr"):
            title_link = tr.select_one("td h2 a")
            date_cell = tr.select_one("td:nth-of-type(2)")
            summary_cell = tr.select_one("td p.mrgn-bttm-0")
            if not title_link or not date_cell:
                continue

            href = (title_link.get("href") or "").strip()
            link = requests.compat.urljoin(url, href)
            date_text = date_cell.get_text(strip=True)
            pub_date = pd.to_datetime(date_text, errors="coerce")
            pub_date_text = "" if pd.isna(pub_date) else pub_date.strftime("%a, %d %b %Y 00:00:00 GMT")
            guid_match = re.search(r"id=(\d+)", link)
            guid = guid_match.group(1) if guid_match else link

            rows.append({
                "guid": guid,
                f"title_{lang}": title_link.get_text(strip=True),
                f"link_{lang}": link,
                f"description_{lang}": (summary_cell.get_text(strip=True) if summary_cell else ""),
                f"pubDate_{lang}": pub_date_text,
            })

        return pd.DataFrame(rows)

    def load_lang_feed(lang):
        parsed = parse_feedparser(FEEDS[lang], lang)
        if parsed is not None and not parsed.empty:
            return parsed

        print(f"Primary {lang} feed unavailable. Falling back to instrument feeds.")
        fallback = parse_fallback_feeds(lang)
        if not fallback.empty:
            return fallback

        print(f"Fallback instrument feeds unavailable for {lang}. Falling back to modifications table.")
        table_fallback = parse_modifications_table(lang)
        if not table_fallback.empty:
            return table_fallback

        # Keep the original parser as a final last-resort attempt to preserve behaviour.
        return parse_rss(FEEDS[lang], lang)

    en = load_lang_feed("en")
    fr = load_lang_feed("fr")

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
