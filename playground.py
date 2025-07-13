from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.agents.models import ListSortOrder
from dotenv import load_dotenv

load_dotenv()

credentials = DefaultAzureCredential()

project = AIProjectClient(
    credential=credentials,
    endpoint="https://sara-openai-underwritin-resource.services.ai.azure.com/api/projects/sara-openai-underwritin-project")

agent = project.agents.get_agent("asst_0N9JnFU6reHLbJqS4wMbysEu")

thread = project.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hi SME UK Underwriting AI Agent"
)

run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id)

if run.status == "failed":
    print(f"Run failed: {run.last_error}")
else:
    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

    for message in messages:
        if message.text_messages:
            print(f"{message.role}: {message.text_messages[-1].text.value}")