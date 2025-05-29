# RSS Feed Fetcher

This repository automates fetching the TBS SCT RSS feed and tracking items in a CSV.

## Usage
1. Configure a GitHub Action (pre-built in `.github/workflows/fetch_rss.yml`).
2. Ensure `secrets.GITHUB_TOKEN` is available.

The workflow runs on a schedule to:
- Fetch the RSS feed.
- Append new items to `data/items.csv`.
- Create a GitHub Issue for each newly discovered item.
