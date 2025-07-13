# app.py
import time
import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from azure.identity import ClientSecretCredential
from azure.core.exceptions import HttpResponseError

# ─── CONFIG ──────────────────────────────────────────────────────────
ENDPOINT = st.secrets["azure"]["endpoint"]
AGENT_ID = st.secrets["azure"]["agent_id"]
AZURE_TENANT_ID = st.secrets["azure"]["tenant"]
AZURE_CLIENT_ID = st.secrets["azure"]["client"]
AZURE_CLIENT_SECRET = st.secrets["azure"]["secret"]

#credentials = DefaultAzureCredential()

st.set_page_config(page_title="SME Underwriting AI Agent", page_icon="🤖")
st.title("SME UK Underwriting AI Agent")

@st.cache_resource(show_spinner="🔑 Authenticating with Azure…")
def get_agent_client():
    cred = ClientSecretCredential(
        tenant_id=AZURE_TENANT_ID,
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET
    )
    # this will raise if the identity has no token source
    client = AIProjectClient(
        credential=cred,
        endpoint=ENDPOINT
    )
    agent  = client.agents.get_agent(AGENT_ID)  # raises if IDs mismatch / no RBAC
    return client, agent

# ---------------------------------------------------------------------------
# 4.  Helper: send a prompt → get assistant reply
# ---------------------------------------------------------------------------
def ask_agent(prompt: str) -> str:
    client, agent = get_agent_client()

    # (a) create a thread
    th = client.agents.threads.create()
    print(f"Created thread, ID: {th.id}")

    # (b) post user message
    client.agents.messages.create(th.id, role="user", content=prompt)
    print(f"User message sent: {prompt}")

    # Kick off run & poll until done
    run = client.agents.runs.create_and_process(
        thread_id=th.id,
        agent_id=agent.id)
    
    print(f"Run status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
        raise RuntimeError(run.last_error["message"])

    # (d) read assistant reply
    msgs = client.agents.messages.list(
        th.id, order=ListSortOrder.ASCENDING, limit=20
    )
    for message in msgs:
        if message.text_messages and message.role == "assistant":
            return message.text_messages[-1].text.value
    return "(no reply)"


# ---------------------------------------------------------------------------
# 5.  Streamlit chat interface
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# replay history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Ask the agent …")

if user_prompt:
    st.session_state.history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = ask_agent(user_prompt)
            except HttpResponseError as e:
                reply = f"⚠️ Azure error:\n```\n{e.message}\n```"
            except Exception as e:
                reply = f"⚠️ {e}"
        st.markdown(reply)

    st.session_state.history.append({"role": "assistant", "content": reply})




# if "history" not in st.session_state:
#     st.session_state.history = []

# with st.form("chat_form", clear_on_submit=True):
#     user_input = st.text_input("You:")
#     submitted = st.form_submit_button("Send")

# if submitted and user_input:
#     st.session_state.history.append(("user", user_input))

#     # 1. Retrieve agent & start thread
#     agent = project.agents.get_agent(AGENT_ID)
#     thread = project.agents.threads.create()
#     print(f"Created thread, ID: {thread.id}")

#     # 2. Send user message
#     #project.agents.messages.create(thread.id, "user", user_input)
#     print(f"User message sent: {user_input}")
#     message = project.agents.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content=user_input
#     )

#     # 3. Kick off run & poll until done
#     run = project.agents.runs.create_and_process(
#         thread_id=thread.id,
#         agent_id=agent.id)
    
#     if run.status == "failed":
#         print(f"Run failed: {run.last_error}")
#     else:
#         messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

#     # 4. Fetch all messages & append
#     #st.session_state.history.append(("assistant", "Processing..."))
#     for message in messages:
#         if message.text_messages:
#             print(f"{message.role}: {message.text_messages[-1].text.value}")
#             st.session_state.history.append((message.role, message.text_messages[-1].text.value))

# # Render chat history
# for role, text in st.session_state.history:
#     color = "blue" if role == "user" else "green"
#     st.markdown(f"<p style='color:{color}'><b>{role}:</b> {text}</p>", unsafe_allow_html=True)