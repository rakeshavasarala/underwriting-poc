# app.py
import time
import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from azure.ai.agents.models import ListSortOrder
from azure.core.exceptions import HttpResponseError

# ─── CONFIG ──────────────────────────────────────────────────────────
ENDPOINT      = st.secrets["azure"]["endpoint"]
AGENT_ID      = st.secrets["azure"]["agent_id"]
TENANT_ID     = st.secrets["azure"]["tenant"]
CLIENT_ID     = st.secrets["azure"]["client"]
CLIENT_SECRET = st.secrets["azure"]["secret"]

st.set_page_config(page_title="SME Underwriting AI Agent", page_icon="🤖")
st.title("SME UK Underwriting AI Agent")

@st.cache_resource(show_spinner="🔑 Authenticating with Azure…")
def get_client_and_agent():
    cred = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    client = AIProjectClient(endpoint=ENDPOINT, credential=cred)
    agent  = client.agents.get_agent(AGENT_ID)
    return client, agent

# ─── Thread setup ─────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    client, agent = get_client_and_agent()
    thread = client.agents.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.agent_id  = agent.id

# Always show the current thread ID at the top
st.markdown(f"**🔖 Thread ID:** `{st.session_state.thread_id}`")

# ─── ask_agent helper ─────────────────────────────────────────────────
def ask_agent(prompt: str) -> str:
    client, agent = get_client_and_agent()
    thread_id = st.session_state.thread_id

    # post user message
    client.agents.messages.create(thread_id, role="user", content=prompt)

    # run & poll
    run = client.agents.runs.create_and_process(
        thread_id=thread_id,
        agent_id=agent.id
    )
    if run.status == "failed":
        raise RuntimeError(run.last_error["message"])

    # fetch assistant reply
    msgs = client.agents.messages.list(
        thread_id, order=ListSortOrder.ASCENDING, limit=20
    )
    for msg in msgs:
        if msg.role == "assistant" and msg.text_messages:
            return msg.text_messages[-1].text.value
    return "(no reply)"

# ─── Streamlit chat interface ─────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# replay chat history, annotating user messages with thread ID
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "user":
            st.caption(f"Thread ID: {st.session_state.thread_id}")

# new user input
if user_prompt := st.chat_input("Ask the agent …"):
    # record & display user input
    st.session_state.history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        st.caption(f"Thread ID: {st.session_state.thread_id}")

    # get and display assistant reply
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
