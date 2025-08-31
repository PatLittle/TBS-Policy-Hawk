import os
import json
import re
import difflib
import subprocess
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import tiktoken

# --- Configuration ---
# Can be overridden by command-line arguments
DEFAULT_MODEL = "openai/gpt-5"
DEFAULT_DATA_DIR = "data"
DEFAULT_ISSUE_MAP_FILE = "data/issue_map.json"
DEFAULT_OUTPUT_FILE = "grok-diff.md"
DEFAULT_MAX_TOKENS = 100000  # Increased for modern models
API_ENDPOINT = "https://models.github.ai/inference"

# --- Helper Functions ---

def get_client():
    """Initializes and returns the AI client."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set.")
    return ChatCompletionsClient(
        endpoint=API_ENDPOINT,
        credential=AzureKeyCredential(token),
    )

def discover_file_pairs(data_dir):
    """
    Automatically discovers pairs of XML files based on a filename pattern.
    A pair represents an older and a newer version of the same document.
    """
    pattern = re.compile(r"^(.*?)_(\d{4}-\d{2}-\d{2})\.xml$")
    files = defaultdict(list)
    for root, _, filenames in os.walk(data_dir):
        for fname in filenames:
            if fname.endswith(".xml"):
                match = pattern.match(fname)
                if match:
                    # Group by document ID, which is part of the prefix
                    doc_id_match = re.search(r'_(\d+)_', match.group(1))
                    if doc_id_match:
                        prefix_key = os.path.join(root, match.group(1))
                        files[prefix_key].append(os.path.join(root, fname))

    pairs = []
    for prefix, flist in files.items():
        if len(flist) >= 2:
            flist.sort(key=lambda x: re.search(r'(\d{4}-\d{2}-\d{2})\.xml$', x).group(1), reverse=True)
            # We only compare the most recent with the one just before it.
            pairs.append((flist[0], flist[1]))
    
    print(f"Found {len(pairs)} file pair(s) to compare.")
    return pairs

def get_ai_summary(client, model, text_new, text_old, file_new, file_old, max_tokens):
    """
    Generates a summary of changes between two texts using an AI model.
    Handles large documents by chunking.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens_new = encoding.encode(text_new)
    tokens_old = encoding.encode(text_old)

    if len(tokens_new) + len(tokens_old) < max_tokens:
        print("  Documents are small enough, summarizing in a single call.")
        return summarize_chunk(client, model, text_new, text_old, file_new, file_old)

    # Chunking for large documents
    print(f"  Documents too large, chunking with max_tokens={max_tokens}.")
    chunk_list = list(chunk_pair(encoding, tokens_new, tokens_old, max_tokens))
    total_chunks = len(chunk_list)
    print(f"  Split into {total_chunks} chunk(s).")

    summaries = [None] * total_chunks
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_idx = {
            executor.submit(
                summarize_chunk, client, model, chunk_new, chunk_old, file_new, file_old, idx, total_chunks
            ): idx
            for idx, (chunk_new, chunk_old) in enumerate(chunk_list, start=1)
        }
        for future in as_completed(future_to_idx):
            idx, result = future.result()
            summaries[idx-1] = result

    # Aggregate summaries
    if len(summaries) > 1:
        print("  Aggregating chunk summaries...")
        aggregate_prompt = (
            "\n\n".join(summaries)
            + "\n\n---\n\n"
            "The above are summaries of changes between two versions of a document, broken into several parts. "
            "Please synthesize these partial summaries into a single, cohesive, and comprehensive summary of all the changes. "
            "Start with a high-level executive summary, then provide a detailed breakdown of changes, referencing sections where possible. "
            "The final output should be a single, well-structured markdown document."
        )
        final_response = client.complete(
            messages=[
                SystemMessage("You are a helpful assistant that synthesizes multiple summary sections into one comprehensive document."),
                UserMessage(aggregate_prompt),
            ],
            model=model,
        )
        return final_response.choices[0].message.content
    else:
        return summaries[0]

def chunk_pair(encoding, tokens1, tokens2, max_tokens):
    """Yields paired chunks from both token lists within a combined token limit."""
    step = max_tokens // 2
    i = 0
    while i * step < len(tokens1) or i * step < len(tokens2):
        chunk1_tokens = tokens1[i * step : (i + 1) * step]
        chunk2_tokens = tokens2[i * step : (i + 1) * step]
        yield encoding.decode(chunk1_tokens), encoding.decode(chunk2_tokens)
        i += 1

def summarize_chunk(client, model, chunk_new, chunk_old, new_file, old_file, part_num=1, total_parts=1):
    """Generates a summary for a single pair of text chunks."""
    print(f"    Summarizing chunk {part_num}/{total_parts}...")
    
    prompt = (
        f"Here are two versions of a policy document. Please provide a detailed summary of the changes.\n\n"
        f"Focus on substantive changes to requirements, responsibilities, and procedures. Ignore minor formatting or XML structural changes.\n"
        f"Structure your response in markdown format. Start with an executive summary of the key changes in this chunk, then provide a detailed list of changes, referencing section numbers where possible.\n\n"
        f"DOCUMENT VERSION 1 (Old - from {os.path.basename(old_file)}):\n"
        f"```xml\n{chunk_old}\n```\n\n"
        f"DOCUMENT VERSION 2 (New - from {os.path.basename(new_file)}):\n"
        f"```xml\n{chunk_new}\n```"
    )

    response = client.complete(
        messages=[
            SystemMessage("You are an expert policy analyst assistant. Your task is to compare two versions of a government policy document and summarize the changes clearly and concisely for a policy-savvy audience."),
            UserMessage(prompt),
        ],
        model=model,
    )
    
    content = response.choices[0].message.content
    if total_parts > 1:
        return part_num, f"### Summary for Part {part_num}\n\n" + content
    else:
        return content

def post_comment_to_issue(issue_number, comment_body):
    """Posts a comment to a GitHub issue using the gh CLI."""
    print(f"  Posting analysis to GitHub issue #{issue_number}...")
    try:
        # Truncate body if too long for command line
        max_len = 30000 # A safe limit
        if len(comment_body) > max_len:
            comment_body = comment_body[:max_len] + "\n\n... (comment truncated)"

        subprocess.run(
            [
                "gh",
                "issue",
                "comment",
                str(issue_number),
                "--body",
                comment_body,
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"  Successfully commented on issue #{issue_number}.")
    except subprocess.CalledProcessError as e:
        print(f"  Error posting to GitHub issue #{issue_number}: {e.stderr}")
    except FileNotFoundError:
        print("  'gh' command not found. Skipping GitHub issue comment.")

def main(args):
    """Main function to orchestrate the analysis process."""
    client = get_client()
    file_pairs = discover_file_pairs(args.data_dir)

    if not file_pairs:
        print("No new file pairs to process. Exiting.")
        return

    # Load issue mapping
    try:
        with open(args.issue_map_file, "r", encoding="utf-8") as f:
            issue_map = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Issue map file not found at {args.issue_map_file}. Will not post to issues.")
        issue_map = {}

    full_analysis_content = []

    for i, (new_file, old_file) in enumerate(file_pairs, 1):
        print(f"\n--- Processing pair {i}/{len(file_pairs)} ---")
        print(f"NEW: {os.path.basename(new_file)}")
        print(f"OLD: {os.path.basename(old_file)}")

        with open(new_file, 'r', encoding='utf-8') as f:
            content_new = f.read()
        with open(old_file, 'r', encoding='utf-8') as f:
            content_old = f.read()

        # 1. Get AI Summary
        summary = get_ai_summary(client, args.model, content_new, content_old, new_file, old_file, args.max_tokens)

        # 2. Generate Diff
        diff_text = "".join(
            difflib.unified_diff(
                content_old.splitlines(True),
                content_new.splitlines(True),
                fromfile=os.path.basename(old_file),
                tofile=os.path.basename(new_file),
            )
        )

        # 3. Format Output
        output_for_file = (
            f"## AI-Generated Comparison for `{os.path.basename(new_file)}`\n\n"
            f"Compared against previous version: `{os.path.basename(old_file)}`\n\n"
            f"### Summary of Changes\n\n{summary}\n\n"
            f"### Raw Diff\n\n"
            f"<details><summary>Click to view diff</summary>\n\n"
            f"```diff\n{diff_text}\n```\n\n"
            f"</details>\n"
        )
        full_analysis_content.append(output_for_file)
        print("  Comparison complete.")

        # 4. Post to GitHub Issue
        if args.post_to_github:
            guid_match = re.search(r"_(\d+)_", new_file)
            if guid_match:
                guid = guid_match.group(1)
                issue_number = issue_map.get(guid)
                if issue_number:
                    output_for_issue = (
                        f"An AI-generated analysis of the changes in `{os.path.basename(new_file)}` is available.\n\n"
                        f"### Summary of Changes\n\n{summary}\n\n"
                        f"### Raw Diff\n\n"
                        f"<details><summary>Click to view diff</summary>\n\n"
                        f"```diff\n{diff_text}\n```\n\n"
                        f"</details>\n"
                    )
                    post_comment_to_issue(issue_number, output_for_issue)
                else:
                    print(f"  No issue number found for GUID {guid}. Skipping comment.")
            else:
                print(f"  Could not extract GUID from filename {new_file}. Skipping comment.")

    # 5. Write to output file
    if full_analysis_content:
        final_output = "\n\n---\n\n".join(full_analysis_content)
        mode = "a" if args.append_output else "w"
        if mode == 'a' and not os.path.exists(args.output_file):
            # If appending but file doesn't exist, write header first
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(f"# AI-Generated Policy Document Change Analysis ({args.model})\n\n")
        
        with open(args.output_file, mode, encoding="utf-8") as f:
            if mode == 'a':
                f.write("\n\n---\n\n") # Separator for appended content
            f.write(final_output)
        print(f"\nAnalysis saved to {args.output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare XML policy documents and generate AI summaries.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"AI model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE, help=f"Markdown file to write analysis to (default: {DEFAULT_OUTPUT_FILE})")
    parser.add_argument("--issue-map-file", default=DEFAULT_ISSUE_MAP_FILE, help=f"Path to the issue map JSON file (default: {DEFAULT_ISSUE_MAP_FILE})")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help=f"Directory containing XML files (default: {DEFAULT_DATA_DIR})")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help=f"Max tokens for a single AI call (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument("--post-to-github", action="store_true", help="Post analysis as a comment to the corresponding GitHub issue.")
    parser.add_argument("--append-output", action="store_true", help="Append to the output file instead of overwriting it.")
    
    args = parser.parse_args()
    main(args)
