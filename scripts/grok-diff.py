[import os
import json
import re
import difflib
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import tiktoken

endpoint = "https://models.github.ai/inference"
grok_model = "xai/grok-3"
gpt5_model = "gpt-5"  # Update this string to match your real model name if needed
token = os.environ["GITHUB_TOKEN"]

# Discover pairs of XML files automatically
pattern = re.compile(r"^(.*?)(\d{4}-\d{2}-\d{2})\.xml$")
files = defaultdict(list)
for root, _, filenames in os.walk("data"):
    for fname in filenames:
        if fname.endswith(".xml"):
            m = pattern.match(fname)
            if m:
                prefix = os.path.join(root, m.group(1))
                files[prefix].append(os.path.join(root, fname))

pairs = []
for prefix, flist in files.items():
    if len(flist) >= 2:
        flist.sort(reverse=True)
        pairs.append((flist[0], flist[1]))

print(f"Found {len(pairs)} file pair(s) to compare")

# Load issue mapping (guid -> issue number)
issue_map_path = os.path.join("data", "issue_map.json")
if os.path.isfile(issue_map_path):
    with open(issue_map_path, "r", encoding="utf-8") as f:
        issue_map = json.load(f)
else:
    issue_map = {}

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

encoding = tiktoken.get_encoding("cl100k_base")

def chunk_pair(text1: str, text2: str, max_tokens: int = 3000):
    """Yield paired chunks from both texts within a combined token limit."""
    step = max_tokens // 2
    tokens1 = encoding.encode(text1)
    tokens2 = encoding.encode(text2)
    i = 0
    while i * step < len(tokens1) or i * step < len(tokens2):
        chunk1_tokens = tokens1[i * step : (i + 1) * step]
        chunk2_tokens = tokens2[i * step : (i + 1) * step]
        yield encoding.decode(chunk1_tokens), encoding.decode(chunk2_tokens)
        i += 1

def summarize_chunk(idx, chunk_new, chunk_old, new_file, old_file, total_chunks, model):
    print(f"  Summarizing chunk {idx}/{total_chunks} with model {model}")
    part_message = (
        f"**{os.path.basename(new_file)} (part {idx})**\n```\n{chunk_new}\n```\n\n"
        f"**{os.path.basename(old_file)} (part {idx})**\n```\n{chunk_old}\n```\n\n"
        "These are two versions of the same file to compare. "
        "Summarize the changes to content in the versions, focus on the substance of the document not the xml layout or markup. "
        "Give first an executive summary describing the theme of the changes and major changes to requirements, then detailed changes referring to which "
        "sections each change is in, show previous wording and new wording where useful. This is for a policy wonk audience. Generate the output as a markdown document."
    )
    response = client.complete(
        messages=[
            SystemMessage(
                "You are a helpful assistant that summarizes the changes between versions of a document."
            ),
            UserMessage(part_message),
        ],
        temperature=1.0,
        top_p=1.0,
        model=model,
    )
    return idx, response.choices[0].message.content

def process_pairs(model, output_filename, post_github=False):
    all_outputs = ""
    for pair_index, (new_file, old_file) in enumerate(pairs, start=1):
        print(
            f"Processing pair {pair_index}/{len(pairs)}: {os.path.basename(new_file)} vs {os.path.basename(old_file)} with model {model}"
        )

        contents = []
        for fp in (new_file, old_file):
            with open(fp, encoding="utf-8") as infile:
                contents.append(infile.read().strip())

        chunk_list = list(chunk_pair(contents[0], contents[1]))
        print(f"  Split into {len(chunk_list)} chunk(s)")

        summaries = [None] * len(chunk_list)
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_idx = {
                executor.submit(
                    summarize_chunk, idx, chunk_new, chunk_old, new_file, old_file, len(chunk_list), model
                ): idx-1
                for idx, (chunk_new, chunk_old) in enumerate(chunk_list, start=1)
            }
            for future in as_completed(future_to_idx):
                idx, result = future.result()
                summaries[idx-1] = result

        if len(summaries) > 1:
            aggregate_prompt = (
                "\n\n".join(summaries)
                + "\n\nCombine the above section summaries into an overall summary of the changes."
            )
            final_response = client.complete(
                messages=[
                    SystemMessage(
                        "You are a helpful assistant that summarizes the changes between versions of a document."
                    ),
                    UserMessage(aggregate_prompt),
                ],
                temperature=1.0,
                top_p=1.0,
                model=model,
            )
            summary = final_response.choices[0].message.content
        else:
            summary = summaries[0]

        diff_text = "".join(
            difflib.unified_diff(
                contents[1].splitlines(True),
                contents[0].splitlines(True),
                fromfile=os.path.basename(old_file),
                tofile=os.path.basename(new_file),
            )
        )

        output = f"# AI Generated Comparison for {os.path.basename(new_file)} and {os.path.basename(old_file)}\n\n"
        output += summary + "\n\n## Diff\n```diff\n" + diff_text + "```\n\n---\n\n"
        all_outputs += output

        print("  Comparison complete")

        # Only post to GitHub for the original run (optional)
        if post_github:
            guid_match = re.search(r"_(\d+)_\d{4}-\d{2}-\d{2}\.xml$", new_file)
            if guid_match:
                guid = guid_match.group(1)
                issue_number = issue_map.get(guid)
                if issue_number:
                    try:
                        subprocess.run(
                            [
                                "gh",
                                "issue",
                                "comment",
                                str(issue_number),
                                "--body",
                                output,
                            ],
                            check=True,
                        )
                    except subprocess.CalledProcessError:
                        pass

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(all_outputs)
    print(f"Output saved as {output_filename}")

    # Only update the README for the original output
    if post_github:
        README_FILE = "README.md"
        MARKER_START = "<!-- BEGIN GROK DIFF -->"
        MARKER_END = "<!-- END GROK DIFF -->"
        with open(README_FILE, "r", encoding="utf-8") as f:
            readme_contents = f.read()
        new_section = f"{MARKER_START}\n{all_outputs}\n{MARKER_END}"
        pattern = re.compile(rf"{MARKER_START}.*?{MARKER_END}", re.DOTALL)
        if pattern.search(readme_contents):
            new_readme = pattern.sub(new_section, readme_contents)
        else:
            new_readme = readme_contents.strip() + "\n\n" + new_section
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(new_readme)

if __name__ == "__main__":
    # First run: GROK-3, updates README and posts to GitHub issues as before
    process_pairs(grok_model, "grok-diff.md", post_github=True)
    # Second run: GPT-5, only creates gpt5-diff.md
    process_pairs(gpt5_model, "gpt5-diff.md", post_github=False)
