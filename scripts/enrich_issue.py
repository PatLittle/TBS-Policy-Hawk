#!/usr/bin/env python3

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse

import requests
from github import Github

try:
    # PyGithub >= 2.x
    from github import Auth
except Exception:  # pragma: no cover
    Auth = None
from playwright.sync_api import sync_playwright

try:
    from markitdown import MarkItDown
except Exception:  # pragma: no cover - handled at runtime
    MarkItDown = None
try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - handled at runtime
    genai = None
    types = None


DATA_DIR = Path("data")
SCREENSHOTS_DIR = Path("screenshots")
SCD2_PATH = DATA_DIR / "tbs_policy_feed_scd2.csv"

COMMENT_MARKERS = {
    "screenshot": "<!-- policy-hawk:screenshot -->",
    "current_md": "<!-- policy-hawk:current-markdown -->",
    "previous_md": "<!-- policy-hawk:previous-markdown -->",
    "diff": "<!-- policy-hawk:diff -->",
    "summary": "<!-- policy-hawk:summary -->",
}

def make_github_client(token: str) -> Github:
    """
    Create a PyGithub client without using deprecated login_or_token.
    Falls back for older PyGithub versions.
    """
    if Auth is not None:
        return Github(auth=Auth.Token(token))
    # Fallback for older PyGithub that may not have Auth
    return Github(token)

def load_event_payload(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_issue_metadata(body: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    link = _match_field(body, r"^\*\*Link:\*\*\s*(\S+)")
    if not link:
        url_match = re.search(r"https?://\S+", body)
        link = url_match.group(0) if url_match else None
    category = _match_field(body, r"^\*\*Category:\*\*\s*(.+)$")
    guid = _match_field(body, r"^\*\*GUID:\*\*\s*(.+)$")
    return link, category, guid


def _match_field(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def ensure_section_html(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["section"] = ["HTML"]
    new_query = urlencode(query, doseq=True)
    scheme = parsed.scheme or "https"
    if scheme == "http":
        scheme = "https"
    return urlunparse(parsed._replace(query=new_query, scheme=scheme))


def fetch_html(url: str) -> str:
    headers = {"User-Agent": "policy-hawk/1.0"}
    if url.startswith("https://corsproxy.io/"):
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        return resp.text

    try:
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        proxy_url = f"https://corsproxy.io/?url={quote(url, safe='')}"
        print(f"Direct fetch failed, retrying via proxy: {proxy_url} ({exc})")
        resp = requests.get(proxy_url, timeout=60, headers=headers)
        resp.raise_for_status()
        return resp.text


def take_screenshot(url: str, filepath: Path) -> bool:
    WINDOWS11_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def attempt(target_url: str) -> bool:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(user_agent=WINDOWS11_UA)
                page.goto(target_url, wait_until="networkidle", timeout=60000)
                page.screenshot(path=str(filepath), full_page=True)
                browser.close()
            return True
        except Exception as exc:  # pragma: no cover - runtime behavior
            print(f"Screenshot error for {target_url}: {exc}")
            return False

    if attempt(url):
        return True
    if url.startswith("http://"):
        return attempt("https://" + url[len("http://") :])
    return False


def html_to_markdown(html_text: str) -> str:
    if MarkItDown is None:
        raise RuntimeError("markitdown is not installed. Install it with pip.")
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "current.html"
        html_path.write_text(html_text, encoding="utf-8")
        md = MarkItDown()
        result = md.convert(str(html_path))
        text_content = getattr(result, "text_content", None) or getattr(result, "text", None)
        if not text_content:
            raise RuntimeError("markitdown returned empty output.")
        return text_content


def find_previous_markdown(base_dir: Path, current_md_path: Path) -> Optional[Path]:
    if not base_dir.exists():
        return None
    candidates = [p for p in base_dir.glob("*.md") if p != current_md_path]
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1]


def compute_diff(old_text: str, new_text: str) -> str:
    import difflib

    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile="previous.md",
        tofile="current.md",
        lineterm="",
    )
    return "\n".join(diff)


def generate_gemini_summary(api_key: str, system_prompt: str, user_prompt: str, model: str) -> str:
    if genai is None or types is None:
        raise RuntimeError("google-genai is not installed. Install it with pip.")
    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)],
        )
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        system_instruction=[types.Part.from_text(text=system_prompt)],
    )
    chunks = []
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            chunks.append(chunk.text)
    summary = "".join(chunks).strip()
    if not summary:
        raise RuntimeError("Gemini returned empty output.")
    return summary


def build_summary_prompt(current_md: str, previous_md: str, diff_md: str) -> str:
    return (
        "Task: Summarize changes between two versions of a TBS policy document.\n\n"
        "Audience: Expert policy analysts.\n"
        "Tone: Formal, precise, and actionable.\n\n"
        "Inputs:\n"
        "1) Current version (markdown):\n"
        f"{current_md}\n\n"
        "2) Previous version (markdown):\n"
        f"{previous_md}\n\n"
        "3) Diff (markdown or unified diff):\n"
        f"{diff_md}\n\n"
        "Output format (markdown):\n"
        "## High-Level Takeaways\n"
        "- ...\n\n"
        "## Clause-Level Changes\n"
        "- [Section/Heading] ...\n\n"
        "## Notable Additions\n"
        "- ...\n\n"
        "## Notable Removals\n"
        "- ...\n\n"
        "## Potential Impacts\n"
        "- ...\n"
    )


def post_comment(issue, body: str, marker: str) -> None:
    if marker in body:
        issue.create_comment(body)
        return
    issue.create_comment(f"{marker}\n{body}")


def comment_exists(issue, marker: str) -> bool:
    for comment in issue.get_comments():
        if marker in (comment.body or ""):
            return True
    return False


def truncate_comment(text: str, limit: int = 60000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n...(truncated)"


def main() -> None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")
    default_branch = "main"
    issue_number = None
    issue_body = ""

    if event_path and Path(event_path).exists():
        event = load_event_payload(Path(event_path))
        issue_data = event.get("issue", {})
        issue_number = issue_data.get("number")
        issue_body = issue_data.get("body", "") or ""
        repo_full_name = event.get("repository", {}).get("full_name") or repo_full_name
        default_branch = event.get("repository", {}).get("default_branch", default_branch)

    manual_issue_number = os.environ.get("ISSUE_NUMBER")
    if not issue_number and manual_issue_number:
        issue_number = int(manual_issue_number)

    if not repo_full_name:
        raise RuntimeError("Repository name not found in event payload or environment.")
    if not issue_number:
        raise RuntimeError("Issue number missing from event payload or ISSUE_NUMBER.")

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN not set.")

    gh = make_github_client(github_token)
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    if not issue_body:
        issue_body = issue.body or ""

    link, category, guid = parse_issue_metadata(issue_body)
    if not link:
        raise RuntimeError("Policy link not found in issue body.")
    if not guid:
        raise RuntimeError("GUID not found in issue body.")

    category = (category or "Unknown").strip().replace(" ", "_")

    section_url = ensure_section_html(link)
    html_text = fetch_html(section_url)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_dir = DATA_DIR / category / guid
    base_dir.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    current_html_path = base_dir / f"{timestamp}.html"
    current_md_path = base_dir / f"{timestamp}.md"
    current_html_path.write_text(html_text, encoding="utf-8")

    current_md = html_to_markdown(html_text)
    current_md_path.write_text(current_md, encoding="utf-8")

    previous_md_path = find_previous_markdown(base_dir, current_md_path)
    previous_md = ""
    if previous_md_path and previous_md_path.exists():
        previous_md = previous_md_path.read_text(encoding="utf-8")

    diff_text = ""
    if previous_md:
        diff_text = compute_diff(previous_md, current_md)
        diff_path = base_dir / f"{timestamp}.diff"
        diff_path.write_text(diff_text, encoding="utf-8")

    screenshot_path = SCREENSHOTS_DIR / f"{guid.replace('/', '_')}.png"
    take_screenshot(link, screenshot_path)
    screenshot_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{screenshot_path.as_posix()}"

    section_url = ensure_section_html(link)
    html_text = fetch_html(section_url)

    if not comment_exists(issue, COMMENT_MARKERS["screenshot"]):
        body = f"### Screenshot\n\n![Screenshot]({screenshot_url})"
        post_comment(issue, body, COMMENT_MARKERS["screenshot"])

    if not comment_exists(issue, COMMENT_MARKERS["current_md"]):
        body = f"### Current Version (Markdown)\n\n{truncate_comment(current_md)}"
        post_comment(issue, body, COMMENT_MARKERS["current_md"])

    if previous_md and not comment_exists(issue, COMMENT_MARKERS["previous_md"]):
        body = f"### Previous Version (Markdown)\n\n{truncate_comment(previous_md)}"
        post_comment(issue, body, COMMENT_MARKERS["previous_md"])

    if diff_text and not comment_exists(issue, COMMENT_MARKERS["diff"]):
        diff_body = (
            "### Diff\n\n"
            "<details><summary>View diff</summary>\n\n"
            f"```diff\n{truncate_comment(diff_text)}\n```\n\n"
            "</details>"
        )
        post_comment(issue, diff_body, COMMENT_MARKERS["diff"])

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and previous_md and diff_text and not comment_exists(issue, COMMENT_MARKERS["summary"]):
        system_prompt = (
            "You are an expert Canadian federal policy analyst. Write concise, evidence-based "
            "change summaries for policy updates. Avoid speculation, cite clauses by heading if "
            "available, and separate high-level takeaways from clause-level details."
        )
        user_prompt = build_summary_prompt(current_md, previous_md, diff_text)
        model = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
        summary = generate_gemini_summary(gemini_key, system_prompt, user_prompt, model)
        summary_path = base_dir / f"{timestamp}.summary.md"
        summary_path.write_text(summary, encoding="utf-8")
        body = f"### Expert Summary of Changes\n\n{summary}"
        post_comment(issue, body, COMMENT_MARKERS["summary"])


if __name__ == "__main__":
    main()
