# app.py
import time
import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, AzureKeyCredential
from azure.ai.agents.models import ListSortOrder

# ─── CONFIG ──────────────────────────────────────────────────────────
ENDPOINT = st.secrets["azure"]["endpoint"]
AGENT_ID = st.secrets["azure"]["agent_id"]

# credential = DefaultAzureCredential()
credentials = DefaultAzureCredential()
#credentials = AzureKeyCredential(API_KEY)

project = AIProjectClient(
    credential=credentials,
    endpoint="https://sara-openai-underwritin-resource.services.ai.azure.com/api/projects/sara-openai-underwritin-project")


st.title("✈️ Undertwriting Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.history.append(("user", user_input))

    # 1. Retrieve agent & start thread
    agent = project.agents.get_agent(AGENT_ID)
    thread = project.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # 2. Send user message
    #project.agents.messages.create(thread.id, "user", user_input)
    print(f"User message sent: {user_input}")
    message = project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    # 3. Kick off run & poll until done
    run = project.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id)
    
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    else:
        messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

    # 4. Fetch all messages & append
    #st.session_state.history.append(("assistant", "Processing..."))
    for message in messages:
        if message.text_messages:
            print(f"{message.role}: {message.text_messages[-1].text.value}")
            st.session_state.history.append((message.role, message.text_messages[-1].text.value))

# Render chat history
for role, text in st.session_state.history:
    color = "blue" if role == "user" else "green"
    st.markdown(f"<p style='color:{color}'><b>{role}:</b> {text}</p>", unsafe_allow_html=True)