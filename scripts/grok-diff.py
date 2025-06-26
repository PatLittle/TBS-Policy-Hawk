import os
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "xai/grok-3"
token = os.environ["GITHUB_TOKEN"]

# Helper function to trim content to N characters (adjust as needed)
def trim_content(content, max_chars=2500):
    if len(content) > max_chars:
        return content[:max_chars//2] + "\n...\n" + content[-max_chars//2:]
    return content

with open("pairs.json") as f:
    pairs = json.load(f)

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

all_outputs = ""

for pair in pairs:
    message = ""
    for file_path in pair:
        filename = os.path.basename(file_path)
        with open(file_path, encoding="utf-8") as infile:
            content = infile.read().strip()
        content = trim_content(content)  # Trim to avoid token overflow
        message += f"**{filename}**\n```\n{content}\n```\n\n"

    message += (
        "These are two versions of the same file to compare. "
        "Summarize the changes to content in the versions, focus on the substance of the document not the xml layout or markup. give "
        "first an executive summary describing the theme of the changes and major changes to requirements, then detailed changes referring to which "
        "sections each change is in, show previous wording and new wording where "
        "useful. This is for a policy wonk audience. Generate the output as a markdown document."
    )

    response = client.complete(
        messages=[
            SystemMessage("You are a helpful assistant that summarizes the changes between versions of a document."),
            UserMessage(message),
        ],
        temperature=1.0,
        top_p=1.0,
        model=model
    )

    summary = response.choices[0].message.content
    all_outputs += f"# Comparison for {os.path.basename(pair[0])} and {os.path.basename(pair[1])}\n\n"
    all_outputs += AI Generated summary + "\n\n---\n\n"

with open("./grok-diff.md", "w", encoding="utf-8") as f:
    f.write(all_outputs)

print("Output saved as grok-diff.md")

import re

README_FILE = "README.md"
MARKER_START = "<!-- BEGIN GROK DIFF -->"
MARKER_END = "<!-- END GROK DIFF -->"

with open(README_FILE, "r", encoding="utf-8") as f:
    readme_contents = f.read()

# Build the new section content
new_section = f"{MARKER_START}\n{all_outputs}\n{MARKER_END}"

# Replace the section between the markers
pattern = re.compile(
    rf"{MARKER_START}.*?{MARKER_END}", re.DOTALL
)
if pattern.search(readme_contents):
    new_readme = pattern.sub(new_section, readme_contents)
else:
    # If section doesn't exist, append at the end
    new_readme = readme_contents.strip() + "\n\n" + new_section

with open(README_FILE, "w", encoding="utf-8") as f:
    f.write(new_readme)
