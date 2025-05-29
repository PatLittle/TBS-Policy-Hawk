# scripts/init_policy_framework_xml_archive.py

import os
import re
import requests
import feedparser

# Feeds and corresponding target directories
feeds = {
    "Framework": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=79",
    "Policy": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=27",
    "Directive": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=73",
    "Standard": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=36",
    "Guideline": "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=83"
}

def sanitize_filename(filename):
    # Remove/replace invalid filename characters
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)

for dir_name, feed_url in feeds.items():
    target_dir = os.path.join('data', dir_name)
    os.makedirs(target_dir, exist_ok=True)
    print(f"Processing {dir_name} feed...")

    # Parse feed
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        # Use HTTPS and add &section=xml
        xml_url = entry.link.replace("http://", "https://") + "&section=xml"

        title = entry.title
        guid = entry.id if 'id' in entry else entry.guid
        filename = f"{sanitize_filename(title)}_{sanitize_filename(guid)}.xml"
        filepath = os.path.join(target_dir, filename)

        if os.path.exists(filepath):
            print(f"Already downloaded: {filepath}")
            continue

        try:
            resp = requests.get(xml_url)
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                print(f"Downloaded: {filepath}")
            else:
                print(f"Failed to download: {xml_url} (status: {resp.status_code})")
        except Exception as e:
            print(f"Error downloading {xml_url}: {e}")
