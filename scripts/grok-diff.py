import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.github.ai/inference"
model = "xai/grok-3-mini"
token = os.environ["GITHUB_TOKEN"]
input = "./pairs.json"

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

response = client.complete(
    messages=[
        SystemMessage("You are a helpful assistant that summarizes the changes between versions of a document."),
      UserMessage(input +"is a list of pair of 2 versions of the same file to compare.
      Summarize the difference between the content in the versions, and give
      first an executive summary, then detailed changes referring to which
      sections each change is in, show previous wording and new wording where
      useful. This is for a policy wonk audience"),
    ],
    temperature=1.0,
    top_p=1.0,
    model=model
)

print(response.choices[0].message.content)

