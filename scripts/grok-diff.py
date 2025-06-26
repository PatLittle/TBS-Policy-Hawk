import os
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "xai/grok-3"
token = os.environ["GITHUB_TOKEN"]

# Load file pairs
with open("pairs.json") as f:
    pairs = json.load(f)

message = ""
for pair in pairs:
    for file_path in pair:
        filename = os.path.basename(file_path)
        with open(file_path, encoding="utf-8") as infile:
            content = infile.read().strip()
        message += f"**{filename}**\n```\n{content}\n```\n\n"

message += (
    "These are pairs of files (old and new versions) to compare. "
    "Summarize the difference between the content in the versions, and give "
    "first an executive summary, then detailed changes referring to which "
    "sections each change is in, show previous wording and new wording where "
    "useful. This is for a policy wonk audience. Generate the output as a markdown document."
)

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
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

print(response.choices[0].message.content)
with open("./grok-diff.md", "w", encoding="utf-8") as f:
    f.write(response.choices[0].message.content)
print("Output saved as grok-diff.md")
