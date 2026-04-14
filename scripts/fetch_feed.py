import os
import csv
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime

# --- Configuration ---
RSS_URL = "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=2&count=100"
USER_AGENT = os.getenv("TBS_POLICY_HAWK_USER_AGENT", "TBS-Policy-Hawk/1.0 (+https://github.com/TBS-Policy-Hawk)")
FALLBACK_RSS_URLS = [
    "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=79",
    "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=27",
    "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=73",
    "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=36",
    "https://www.tbs-sct.canada.ca/pol/rssfeeds-filsrss-eng.aspx?feed=1&type=83",
]
MODIFICATIONS_TABLE_URLS = [
    "https://www.tbs-sct.canada.ca/pol/modifications-eng.aspx",
    "https://www.tbs-sct.canada.ca/pol/modifications-fra.aspx",
]
DATA_DIR = "data"
ITEMS_CSV_PATH = os.path.join(DATA_DIR, "items.csv")
NEW_ITEMS_CSV_PATH = os.path.join(DATA_DIR, "new_items.csv")
CSV_HEADERS = ["guid", "title", "link", "pubDate", "category", "filename", "updated_date"]
FRENCH_CATEGORY_MAP = {
    "Politique": "Policy",
    "Directive": "Directive",
    "Norme": "Standard",
    "Ligne directrice": "Guideline",
    "Lignes directrices": "Guideline",
    "Guide": "Guide",
    "Cadre stratégique": "Framework",
    "Cadre": "Framework",
}

# --- Helper Functions ---

def ensure_dir(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(name):
    """Sanitize a string to be a valid filename."""
    name = name.replace(":", "_").replace("/", "_")
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()


def parse_pub_date(pub_date):
    """Convert an RSS date string to a comparable datetime value."""
    if not pub_date:
        return datetime.min
    try:
        return parsedate_to_datetime(pub_date)
    except (TypeError, ValueError):
        return datetime.min


def normalize_entry(entry):
    """Normalize feedparser entries into a stable dictionary structure."""
    guid = entry.get('guid') or entry.get('id') or entry.get('link')
    return {
        "guid": guid,
        "title": entry.get('title', '').strip(),
        "link": entry.get('link', '').strip(),
        "pubDate": entry.get('published', ''),
        "category": entry.get('category', 'Uncategorized'),
    }


def normalize_category(label):
    """Normalize category labels to repository folder names where possible."""
    if not label:
        return "Uncategorized"
    normalized = label.strip()
    return FRENCH_CATEGORY_MAP.get(normalized, normalized)


def format_iso_date_for_pub_date(date_text):
    """Convert YYYY-MM-DD strings into RSS-like date text for compatibility."""
    try:
        dt = datetime.strptime(date_text.strip(), "%Y-%m-%d")
    except (TypeError, ValueError, AttributeError):
        return ""
    return dt.strftime("%a, %d %b %Y 00:00:00 GMT")


def fetch_entries_from_modifications_table(getter=requests.get):
    """Scrape the modifications table as a last-resort source of updates."""
    for page_url in MODIFICATIONS_TABLE_URLS:
        try:
            response = getter(page_url, timeout=30, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Warning: unable to retrieve modifications table ({page_url}): {exc}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="results-table")
        if not table:
            print(f"Warning: modifications table not found on {page_url}")
            continue

        entries = []
        rows = table.select("tbody tr")
        for row in rows:
            title_link = row.select_one("td h2 a")
            date_cell = row.select_one("td:nth-of-type(2)")
            metadata = row.select_one("td p.text-muted")

            if not title_link or not date_cell:
                continue

            title = title_link.get_text(strip=True)
            link = requests.compat.urljoin(page_url, title_link.get("href", "").strip())
            date_text = date_cell.get_text(strip=True)
            category_text = "Uncategorized"
            if metadata:
                category_text = metadata.get_text(" ", strip=True).split("|", 1)[0].strip()

            doc_id_match = re.search(r"id=(\d+)", link)
            guid = doc_id_match.group(1) if doc_id_match else link

            entries.append({
                "guid": guid,
                "title": title,
                "link": link,
                "pubDate": format_iso_date_for_pub_date(date_text),
                "category": normalize_category(category_text),
            })

        if entries:
            return entries

    return []


def fetch_entries_with_fallback(parser=feedparser.parse):
    """Fetch entries from primary feed; use instrument feeds if main feed is unavailable."""
    def parse_feed(url):
        try:
            return parser(url, request_headers={"User-Agent": USER_AGENT})
        except TypeError:
            return parser(url)

    primary_feed = parse_feed(RSS_URL)
    primary_entries = getattr(primary_feed, 'entries', [])

    if not getattr(primary_feed, 'bozo', False) and primary_entries:
        return [normalize_entry(entry) for entry in primary_entries], "primary"

    if getattr(primary_feed, 'bozo', False):
        print(f"Warning: main RSS feed appears broken ({primary_feed.bozo_exception}). Falling back to instrument feeds.")
    else:
        print("Warning: main RSS feed returned no entries. Falling back to instrument feeds.")

    deduped_entries = {}
    for feed_url in FALLBACK_RSS_URLS:
        fallback_feed = parse_feed(feed_url)
        if getattr(fallback_feed, 'bozo', False):
            print(f"Warning: fallback feed parse issue for {feed_url}: {fallback_feed.bozo_exception}")
            continue
        for entry in getattr(fallback_feed, 'entries', []):
            normalized = normalize_entry(entry)
            guid = normalized['guid']
            if not guid:
                continue
            existing = deduped_entries.get(guid)
            if not existing or parse_pub_date(normalized['pubDate']) > parse_pub_date(existing['pubDate']):
                deduped_entries[guid] = normalized

    sorted_entries = sorted(
        deduped_entries.values(),
        key=lambda e: parse_pub_date(e['pubDate']),
        reverse=True,
    )
    if sorted_entries:
        return sorted_entries, "fallback"

    table_entries = fetch_entries_from_modifications_table()
    if table_entries:
        sorted_table_entries = sorted(
            table_entries,
            key=lambda e: parse_pub_date(e['pubDate']),
            reverse=True,
        )
        return sorted_table_entries, "modifications-table"

    return [], "fallback"

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

        parsed_date = parse_pub_date(pub_date)
        if parsed_date != datetime.min:
            date_str = parsed_date.strftime('%Y-%m-%d')
        else:
            try:
                date_str = datetime.strptime(pub_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except (TypeError, ValueError):
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

    entries, source = fetch_entries_with_fallback()
    if not entries:
        print("Error: unable to fetch entries from both main and fallback RSS feeds.")
        return
    print(f"Using {source} feed source with {len(entries)} entries.")

    new_items = []
    for entry in entries:
        if entry['guid'] not in existing_guids:
            print(f"New item found: {entry['title']} ({entry['guid']})")
            category = entry['category']
            filename = download_policy_xml(entry['link'], category, entry['title'], entry['pubDate'])
            if filename:
                new_items.append({
                    "guid": entry['guid'], "title": entry['title'], "link": entry['link'],
                    "pubDate": entry['pubDate'], "category": category, "filename": filename,
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
