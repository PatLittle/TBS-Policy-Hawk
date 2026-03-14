#!/usr/bin/env python3
"""Fetch Adobe Analytics policy-suite familiarity metrics by department.

This script is designed for the Government of Canada policy-suite use case:
1. Pull page views for each policy instrument URL.
2. Break down each instrument by organization/department dimension.
3. Optionally estimate referral traffic each department drives to each instrument.

Because Adobe Analytics implementations vary, this script includes:
- Dimension discovery (`--discover-dimensions`) to find likely org/department dimensions.
- Configurable dimension IDs for organization, page, and referrer.
- CSV outputs that can feed a BI dashboard for familiarity-gap analysis.

Authentication:
- Preferred: set `ADOBE_ACCESS_TOKEN` (already-minted bearer token).
- Optional fallback: provide client credentials and scopes to request a token.

Environment variables (required unless provided via flags):
- ADOBE_API_KEY
- ADOBE_GLOBAL_COMPANY_ID
- ADOBE_REPORT_SUITE_ID
- ADOBE_ACCESS_TOKEN (or ADOBE_CLIENT_ID + ADOBE_CLIENT_SECRET + ADOBE_SCOPES)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

DEFAULT_INSTRUMENT_CSV = "data/tbs_policy_feed_union_by_guid.csv"
DEFAULT_OUTPUT_DIR = "outputs/adobe_analytics"
DEFAULT_METRIC = "metrics/pageviews"
DEFAULT_PAGE_DIMENSION = "variables/page"
DEFAULT_DATE_RANGE = "2025-01-01T00:00:00.000/2025-12-31T23:59:59.999"


@dataclass
class AdobeConfig:
    api_key: str
    global_company_id: str
    report_suite_id: str
    access_token: str


class AdobeAnalyticsClient:
    def __init__(self, config: AdobeConfig, timeout_seconds: int = 45) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.base_url = f"https://analytics.adobe.io/api/{config.global_company_id}"

    @classmethod
    def from_env_or_args(cls, args: argparse.Namespace) -> "AdobeAnalyticsClient":
        api_key = args.api_key or os.getenv("ADOBE_API_KEY")
        company_id = args.global_company_id or os.getenv("ADOBE_GLOBAL_COMPANY_ID")
        report_suite = args.report_suite_id or os.getenv("ADOBE_REPORT_SUITE_ID")

        access_token = args.access_token or os.getenv("ADOBE_ACCESS_TOKEN")
        if not access_token:
            access_token = mint_access_token(
                client_id=args.client_id or os.getenv("ADOBE_CLIENT_ID"),
                client_secret=args.client_secret or os.getenv("ADOBE_CLIENT_SECRET"),
                scopes=args.scopes or os.getenv("ADOBE_SCOPES"),
            )

        missing = [
            name
            for name, value in [
                ("ADOBE_API_KEY", api_key),
                ("ADOBE_GLOBAL_COMPANY_ID", company_id),
                ("ADOBE_REPORT_SUITE_ID", report_suite),
                ("ADOBE_ACCESS_TOKEN (or client credentials)", access_token),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                "Missing required auth/config values: " + ", ".join(missing)
            )

        return cls(
            AdobeConfig(
                api_key=api_key,
                global_company_id=company_id,
                report_suite_id=report_suite,
                access_token=access_token,
            )
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "x-api-key": self.config.api_key,
            "x-proxy-global-company-id": self.config.global_company_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            headers=self._headers(),
            timeout=self.timeout_seconds,
            **kwargs,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Adobe API error ({response.status_code}) for {url}: {response.text}"
            )
        return response.json()

    def list_dimensions(self) -> List[Dict]:
        page = 0
        all_rows: List[Dict] = []

        while True:
            payload = self._request(
                "GET",
                f"dimensions?rsid={self.config.report_suite_id}&page={page}&limit=100",
            )
            rows = payload.get("content", [])
            all_rows.extend(rows)
            last_page = payload.get("lastPage", True)
            if last_page or not rows:
                break
            page += 1
        return all_rows

    def run_report(
        self,
        *,
        dimension: str,
        metric_id: str,
        date_range: str,
        limit: int,
        metric_filters: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        payload = {
            "rsid": self.config.report_suite_id,
            "globalFilters": [{"type": "dateRange", "dateRange": date_range}],
            "metricContainer": {
                "metrics": [{"id": metric_id}],
            },
            "dimension": dimension,
            "settings": {
                "limit": limit,
                "page": 0,
                "countRepeatInstances": True,
            },
        }

        if metric_filters:
            payload["metricContainer"]["metricFilters"] = metric_filters
            payload["metricContainer"]["metrics"][0]["filters"] = [
                filter_row["id"] for filter_row in metric_filters
            ]

        data = self._request("POST", "reports", json=payload)
        return data.get("rows", [])


def mint_access_token(
    *, client_id: Optional[str], client_secret: Optional[str], scopes: Optional[str]
) -> Optional[str]:
    if not (client_id and client_secret and scopes):
        return None

    token_url = "https://ims-na1.adobelogin.com/ims/token/v3"
    response = requests.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": scopes,
        },
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to mint Adobe access token ({response.status_code}): {response.text}"
        )
    return response.json().get("access_token")


def load_instrument_urls(csv_path: Path, limit: Optional[int] = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required_columns = {"guid", "title_en", "link_en"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Input CSV missing required columns: {sorted(missing)}")

    slim = (
        df[["guid", "title_en", "link_en"]]
        .dropna(subset=["link_en"])
        .drop_duplicates(subset=["guid", "link_en"])
    )
    if limit is not None and limit > 0:
        slim = slim.head(limit)
    return slim


def find_candidate_dimensions(dimensions: Iterable[Dict], keywords: List[str]) -> List[Dict]:
    hits = []
    low_keywords = [k.lower() for k in keywords]
    for dim in dimensions:
        combined = " ".join(
            str(dim.get(field, "")) for field in ["id", "name", "title", "description"]
        ).lower()
        if any(keyword in combined for keyword in low_keywords):
            hits.append(dim)
    return hits


def page_filter_item_id(url: str) -> str:
    # Most Adobe page dimensions key by exact page URL.
    return url


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_department_analysis(client: AdobeAnalyticsClient, args: argparse.Namespace) -> None:
    instruments = load_instrument_urls(Path(args.instrument_csv), args.instrument_limit)
    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

    by_department_rows: List[Dict] = []
    referral_rows: List[Dict] = []

    for index, instrument in instruments.iterrows():
        guid = instrument["guid"]
        title = instrument["title_en"]
        url = instrument["link_en"]
        print(f"[{index+1}/{len(instruments)}] Fetching: {guid} | {title}")

        page_filter = {
            "id": "0",
            "type": "breakdown",
            "dimension": args.page_dimension,
            "itemId": page_filter_item_id(url),
        }

        try:
            department_rows = client.run_report(
                dimension=args.department_dimension,
                metric_id=args.metric_id,
                date_range=args.date_range,
                limit=args.department_limit,
                metric_filters=[page_filter],
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ! Failed department breakdown for {guid}: {exc}")
            continue

        for row in department_rows:
            by_department_rows.append(
                {
                    "guid": guid,
                    "instrument_title": title,
                    "instrument_url": url,
                    "department_item_id": row.get("itemId"),
                    "department_value": row.get("value"),
                    "page_views": float(row.get("data", [0])[0]),
                }
            )

        if args.referrer_dimension:
            for dep in department_rows:
                dep_filter = {
                    "id": "1",
                    "type": "breakdown",
                    "dimension": args.department_dimension,
                    "itemId": dep.get("itemId"),
                }
                try:
                    refs = client.run_report(
                        dimension=args.referrer_dimension,
                        metric_id=args.metric_id,
                        date_range=args.date_range,
                        limit=args.referrer_limit,
                        metric_filters=[page_filter, dep_filter],
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"  ! Failed referral breakdown for dept {dep.get('value')}: {exc}")
                    continue

                # Heuristic ownership check: count referrers that contain the department label.
                dep_name = str(dep.get("value", "")).strip().lower()
                owned_pages = 0
                referral_views = 0.0
                for ref in refs:
                    ref_value = str(ref.get("value", ""))
                    views = float(ref.get("data", [0])[0])
                    referral_views += views
                    if dep_name and dep_name in ref_value.lower():
                        owned_pages += 1

                referral_rows.append(
                    {
                        "guid": guid,
                        "instrument_title": title,
                        "instrument_url": url,
                        "department_item_id": dep.get("itemId"),
                        "department_value": dep.get("value"),
                        "department_views_to_instrument": float(dep.get("data", [0])[0]),
                        "estimated_owned_referrer_pages": owned_pages,
                        "referral_views_from_department": referral_views,
                    }
                )

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    by_department_path = output_dir / "policy_instrument_views_by_department.csv"
    write_csv(by_department_path, by_department_rows)
    print(f"Wrote department view breakdown: {by_department_path}")

    if args.referrer_dimension:
        ref_path = output_dir / "policy_instrument_department_referrals.csv"
        write_csv(ref_path, referral_rows)
        print(f"Wrote department referral summary: {ref_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch policy instrument pageview familiarity metrics from Adobe Analytics "
            "(department/org breakdown + optional referral signal)."
        )
    )

    # Auth / tenant config
    parser.add_argument("--api-key", default=None, help="Adobe API key (or ADOBE_API_KEY)")
    parser.add_argument(
        "--global-company-id",
        default=None,
        help="Adobe global company ID (or ADOBE_GLOBAL_COMPANY_ID)",
    )
    parser.add_argument(
        "--report-suite-id", default=None, help="Adobe report suite ID (or ADOBE_REPORT_SUITE_ID)"
    )
    parser.add_argument(
        "--access-token", default=None, help="Adobe OAuth access token (or ADOBE_ACCESS_TOKEN)"
    )
    parser.add_argument("--client-id", default=None, help="Adobe OAuth client id")
    parser.add_argument("--client-secret", default=None, help="Adobe OAuth client secret")
    parser.add_argument(
        "--scopes",
        default=None,
        help="Comma-separated OAuth scopes for token minting (or ADOBE_SCOPES)",
    )

    # Analysis config
    parser.add_argument("--instrument-csv", default=DEFAULT_INSTRUMENT_CSV)
    parser.add_argument("--instrument-limit", type=int, default=0)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--date-range", default=DEFAULT_DATE_RANGE)
    parser.add_argument("--metric-id", default=DEFAULT_METRIC)
    parser.add_argument("--page-dimension", default=DEFAULT_PAGE_DIMENSION)
    parser.add_argument(
        "--department-dimension",
        default=None,
        help="Dimension ID that identifies department/organization (required unless using --discover-dimensions only)",
    )
    parser.add_argument(
        "--referrer-dimension",
        default="variables/referrer",
        help="Referrer/page-origin dimension; empty string disables referral output",
    )
    parser.add_argument("--department-limit", type=int, default=200)
    parser.add_argument("--referrer-limit", type=int, default=200)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)

    # Discovery mode
    parser.add_argument(
        "--discover-dimensions",
        action="store_true",
        help="List dimensions matching department/org keywords and exit.",
    )
    parser.add_argument(
        "--discovery-keywords",
        default="department,organization,org,ministry,portfolio,government",
        help="Comma-separated keywords for dimension discovery",
    )

    args = parser.parse_args()
    args.instrument_limit = args.instrument_limit if args.instrument_limit > 0 else None
    if args.referrer_dimension == "":
        args.referrer_dimension = None
    return args


def main() -> int:
    args = parse_args()
    try:
        client = AdobeAnalyticsClient.from_env_or_args(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Configuration error: {exc}")
        return 2

    if args.discover_dimensions:
        dims = client.list_dimensions()
        keywords = [k.strip() for k in args.discovery_keywords.split(",") if k.strip()]
        candidates = find_candidate_dimensions(dims, keywords)

        print(f"Found {len(candidates)} candidate dimensions (of {len(dims)} total):")
        for dim in candidates:
            print(
                f"- id={dim.get('id')} | name={dim.get('name')} | title={dim.get('title')}"
            )
        return 0

    if not args.department_dimension:
        print(
            "Missing --department-dimension. Run with --discover-dimensions first to find the right Adobe dimension ID."
        )
        return 2

    run_department_analysis(client, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
