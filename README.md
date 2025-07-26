[![Fetch RSS Feed](https://github.com/PatLittle/TBS-Policy-Hawk/actions/workflows/fetch_rss.yml/badge.svg?branch=main)](https://github.com/PatLittle/TBS-Policy-Hawk/actions/workflows/fetch_rss.yml)
# TBS Policy Hawk - Watching Like a Hawk for Every Policy Suite Update.
<img src="https://github.com/user-attachments/assets/2cade396-76a8-474a-8c17-f0f7ed1e69ab" width="300" height="300">

This repository automates fetching the TBS Policy Suite RSS feed and will create issues when policy docs are added or updated.

Updates over time are added to `items.csv` along with the GUID assigned, so a digest of change history will accure overtime. 

 [![Static Badge](https://img.shields.io/badge/Open%20in%20Flatdata%20Viewer-FF00E8?style=for-the-badge&logo=github&logoColor=black)](https://flatgithub.com/PatLittle/TBS-Policy-Hawk/data/items.csv?filename=data%2Fitems.csv)

## Want Notifications?
- If you want to recieve notifications for updates to the TBS Policy suite you can:
   * "watch" this repo and set notifications to "issues" or
   * subscribe to the RSS feed https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=25 

---

## Features

✅ Fetch and parse the RSS feed for new policy items  
✅ Append new items to `data/items.csv`  
✅ Create GitHub Issues for new items  
✅ Archive XML documents for **Framework**, **Policy**, **Directive**, **Standard**, and **Guideline** categories

---

## To Do:
- [ ] download the xml version of the new or updated policy document, then store it in the correct directory based on the xml <category>
- [ ] generate a narrative summary of different versions of a updated documents, and add that to the issue


## Usage
1. Configure a GitHub Action (pre-built in `.github/workflows/fetch_rss.yml`).
2. Ensure `secrets.GITHUB_TOKEN` is available.

The workflow runs on a schedule to:
- Fetch the RSS feed.
- Append new items to `data/items.csv`.
- Create a GitHub Issue for each newly detected item.
```
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
```

