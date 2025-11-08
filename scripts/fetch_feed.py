import os
import csv
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
RSS_URL = "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=100"
DATA_DIR = "data"
ITEMS_CSV_PATH = os.path.join(DATA_DIR, "items.csv")
NEW_ITEMS_CSV_PATH = os.path.join(DATA_DIR, "new_items.csv")
CSV_HEADERS = ["guid", "title", "link", "pubDate", "category", "filename", "updated_date"]

# --- Helper Functions ---

def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(name):
    """Sanitize a string to be a valid filename."""
    name = name.replace(":", "_").replace("/", "_")
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

def get_existing_guids(filepath):
    """Reads the existing CSV file and returns a set of GUIDs."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return set()
    
    guids = set()
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'guid' not in reader.fieldnames:
            print(f"Warning: 'guid' column not found in {filepath}. The script will treat all feed items as new.")
            return set()
        for row in reader:
            guids.add(row['guid'])
    return guids

def download_policy_xml(url, category, title, pub_date):
    """Downloads the policy HTML from a given URL and saves it to the correct category directory."""
    # Ensure the URL uses https and contains section=html
    url = url.replace("http://", "https://")
    if "section=xml" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}section=html"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml-xml')
        doc_tag = soup.find('doc')
        doc_id = doc_tag['documentID'] if doc_tag and 'documentID' in doc_tag.attrs else None
        
        if not doc_id:
            print(f"Warning: Could not find documentID for '{title}'. Using title for filename.")
            base_filename = sanitize_filename(title)
        else:
            sanitized_title = sanitize_filename(title.replace(' ', '_'))
            base_filename = f"{sanitized_title}_{doc_id}"

        try:
            dt_object = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
            date_str = dt_object.strftime('%Y-%m-%d')
        except ValueError:
            date_str = datetime.now().strftime('%Y-%m-%d')
            print(f"Warning: Could not parse date '{pub_date}'. Using current date.")

        filename = f"{base_filename}_{date_str}.xml"
        
        category_dir = os.path.join(DATA_DIR, category)
        ensure_dir(category_dir)
        
        filepath = os.path.join(category_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        print(f"Downloaded: {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return None

def main():
    """Main function to fetch RSS feed, download new policies, and update CSV."""
    print("Starting policy fetch process...")
    ensure_dir(DATA_DIR)

    existing_guids = get_existing_guids(ITEMS_CSV_PATH)
    print(f"Found {len(existing_guids)} existing policy documents.")

    feed = feedparser.parse(RSS_URL)
    if feed.bozo:
        print(f"Error parsing RSS feed: {feed.bozo_exception}")
        return

    new_items = []
    for entry in feed.entries:
        if entry.guid not in existing_guids:
            print(f"New item found: {entry.title} ({entry.guid})")
            category = entry.get('category', 'Uncategorized')
            filename = download_policy_xml(entry.link, category, entry.title, entry.published)
            if filename:
                new_items.append({
                    "guid": entry.guid, "title": entry.title, "link": entry.link,
                    "pubDate": entry.published, "category": category, "filename": filename,
                    "updated_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

    if not new_items:
        print("No new policy items found.")
        if os.path.exists(NEW_ITEMS_CSV_PATH): os.remove(NEW_ITEMS_CSV_PATH)
        return

    print(f"Found {len(new_items)} new items to add.")
    with open(NEW_ITEMS_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS); writer.writeheader(); writer.writerows(new_items)
    print(f"Created {NEW_ITEMS_CSV_PATH} for issue creation.")

    file_exists = os.path.exists(ITEMS_CSV_PATH) and os.path.getsize(ITEMS_CSV_PATH) > 0
    with open(ITEMS_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists: writer.writeheader()
        writer.writerows(new_items)
    print("Successfully updated items.csv.")

if __name__ == "__main__":
    main()
