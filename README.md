[![Fetch RSS Feed](https://github.com/PatLittle/TBS-Policy-Hawk/actions/workflows/fetch_rss.yml/badge.svg?branch=main)](https://github.com/PatLittle/TBS-Policy-Hawk/actions/workflows/fetch_rss.yml)
# TBS Policy Suite RSS Feed Watcher

This repository automates fetching the TBS Policy Suite RSS feed and will create issues when policy docs are added or updated.

Updates over time are added to `items.csv` along with the GUID assigned, so a digest of change history will accure overtime.  [![Static Badge](https://img.shields.io/badge/Open%20in%20Flatdata%20Viewer-FF00E8?style=for-the-badge&logo=github&logoColor=black)](https://flatgithub.com/PatLittle/TBS-Policy-Hawk/data/items.csv)


.
├── README.md
├── data/
│ ├── Framework/
│ │ ├── ... .xml
│ ├── Policy/
│ │ ├── ... .xml
│ ├── Directive/
│ │ ├── ... .xml
│ ├── Standard/
│ │ ├── ... .xml
│ ├── Guideline/
│ │ ├── ... .xml
│ ├── items.csv
│ ├── new_items.csv
├── scripts/
│ ├── fetch_feed.py
│ ├── init_framework_xml_archive.py #populates the repo with all current policy docs
├── .github/
│ └── workflows/
│ ├── fetch_rss.yml
│ ├── init_framework_xml.yml 

## Usage
1. Configure a GitHub Action (pre-built in `.github/workflows/fetch_rss.yml`).
2. Ensure `secrets.GITHUB_TOKEN` is available.

The workflow runs on a schedule to:
- Fetch the RSS feed.
- Append new items to `data/items.csv`.
- Create a GitHub Issue for each newly discovered item.
