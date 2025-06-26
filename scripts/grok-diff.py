import os
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "xai/grok-3-mini"
token = os.environ["GITHUB_TOKEN"]

# Helper function to trim content to N characters (adjust as needed)
def trim_content(content, max_chars=1500):
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
        "Summarize the difference between the content in the versions, and give "
        "first an executive summary, then detailed changes referring to which "
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
    all_outputs += summary + "\n\n---\n\n"

with open("./grok-diff.md", "w", encoding="utf-8") as f:
    f.write(all_outputs)

print("Output saved as grok-diff.md")
