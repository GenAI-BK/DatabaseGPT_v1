
# file: app.py
import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
import base64

# --- Constants ---
DB_URI = "mssql+pyodbc://@192.168.2.96\\SQL19/BREGLLM?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
TABLES = ["CUSTOMER_INSIGHTS", "AGENT_PERFORMANCE", "GEOGRAPHIC_ANALYSIS", "POLICY_PERFORMANCE"]
SUGGESTIONS = [
    "Which agent collected the most premium but still has a big loss in revenue?",
    "Which states are most profitable — high premiums but low claims?",
    "Which insurance types make the most profit?",
    "Which age group, defined as 18-25, 26-35, 36-45, 46-55, 56-65, and 66+, makes the most claims?",
]



logo_path = "bk-logo.png" 
image_path = "database.png"

def get_logo_base64(logo_path):
    with open(logo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()          

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- Environment Setup ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

def apply_custom_css_and_logo():
    icon_base64 = get_base64_image(image_path)
    logo_base64 = get_logo_base64(logo_path)

    icon_url = f"data:image/png;base64,{icon_base64}"
    logo_url = f"data:image/png;base64,{logo_base64}"

    st.markdown("""
        <style>
        /* General app styling */
        .stApp {
            background-color: #f4faff;
            font-family: 'Segoe UI', sans-serif;
            padding: 0;
        }

        /* Main content container with border and shadow */
        .main > div {
            border: 4px solid #0077aa;
            border-radius: 20px;
            margin: 20px;
            padding: 20px;
            background-color: #ffffffdd;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        /* Logo image positioned at top-left, partially outside container */
        .top-logo {
            position: absolute;
            top: -180px;
            left: 0px;
            width: 180px;
        }

        /* Title box: horizontal flex container for icon + title text */
        .title-box {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 10px auto;
            gap: 10px;
        }

        /* Logo inside the title box */
        .title-box img {
            width: 30px;
            height: 30px;
        }

        /* Title text styling */
        .title-text {
            font-size: 2rem;
            color: #2d709a;
            font-weight: 700;
            text-transform: uppercase;
        }

        /* Subheading below title */
        .subheading {
            text-align: center;
            font-size: 1rem;
            color: #333333;
            margin-bottom: 3rem;  
        }

        /* Suggestion buttons styling */
        .suggestion-button {
            display: block;
            width: 80%;
            margin: 0.3rem auto;
            padding: 0.5rem;
            font-size: 0.5rem;
            background-color: #d9f3ff;
            border: 1px solid #0077aa;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .suggestion-button:hover {
            background-color: #d0ecff;
        }

        /* Text input styling */
        div.stTextInput > div > input {
            border: 2px solid #0077aa !important;
            border-radius: 10px !important;
            padding: 18px !important;
            font-size: 1rem !important;
        }

        /* Button styling */
        div.stButton > button {
            color: black;
            font-weight: bold;
            border-radius: 10px;
            padding: 0.5rem;
            cursor: pointer;
        }

        /* Background override for app */
        .stApp {
            background-color: #f5f5f5;        
        }

        /* Chat input area styling */
        .stChatInput, textarea[data-testid="stChatInputTextArea"] {
            height: 60px;
            font-weight: 600;
        }

        /* Chat message padding */
        .st-emotion-cache-1y34ygi.eht7o1d7 {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
        }

        /* Chat submit button styling */
        button.st-emotion-cache-ocsh0s.e1d5ycv52 {
            border: none;
            background: #267389;
            color: #fff !important;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button.st-emotion-cache-ocsh0s.e1d5ycv52:hover {
            background-color: #005f7a;
        }

        /* Chat message styling: user messages */
        .stChatMessage.st-emotion-cache-1c7y2kd {
            background-color: #005f7a;
            margin-left: auto;
            padding: 0.5rem;
            color: #fff;
        }

        .stChatMessage.st-emotion-cache-1c7y2kd .stChatMessageContent {
            color: #fff !important;
        }

        /* Chat message styling: bot messages */
        .stChatMessage.st-emotion-cache-4oy321.ea2tk8x0 {
            background: rgba(38, 115, 137, 0.1);
        }

        /* Alternate chat messages background */
        div.stChatMessage.ea2tk8x0:nth-child(odd) {
            background: #005f7a;
        }
        div.stChatMessage.ea2tk8x0:nth-child(odd) .st-emotion-cache-1104ytp p {
            color: #fff;
        }

        /* Textarea border color */
        div[data-baseweb="textarea"] {
            border-color: #e7e7e7;
        }
        div[data-baseweb="textarea"]:focus, div[data-baseweb="textarea"].st-c7 {
            border-color: #005f7a;
        }

        /* Chat submit button styling */
        button.e1xgt8o32[data-testid="stChatInputSubmitButton"] {
            width: 60px;
            background: #005f7a;
            height: 100%;
            border-top-right-radius: 15px;
            border-bottom-right-radius: 15px;
            color: #fff;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button.e1xgt8o32[data-testid="stChatInputSubmitButton"]:hover {
            background: #005f7a;
            color: #fff;
        }

        /* Chat message padding */
        .stChatMessage {
            padding: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="title-box">
        <img src="{icon_url}" alt="icon">
        <div class="title-text">Smart data analyzer</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='subheading'>Try asking any of these questions</div>", unsafe_allow_html=True)

    st.markdown(f"<img src='{logo_url}' class='top-logo' />", unsafe_allow_html=True)






# --- SQL Engine and DB ---
@st.cache_resource
def get_sqlalchemy_engine():
    return create_engine(DB_URI)

@st.cache_resource
def get_database():
    return SQLDatabase.from_uri(DB_URI, include_tables=TABLES)

# --- Follow-up Generator ---
def generate_follow_ups(llm, question):
    prompt = f"""
    You are a helpful assistant. Given the following user question, suggest 3 follow-up questions the user might ask related to previous question.

    Original question: "{question}"

    Rules:
     Your task is to generate 3 follow-up questions that:
    - Are directly related to the original question.
    - Can be answered using similar or related data from the database.
    - Help the user explore the topic further based on available database insights.
    - Are phrased in simple English for a non-technical user.
    - Are short and clear.
    -Frame  such type of question which do not  include reasoning.
    - Do not repeat the original question.

    Respond with a numbered list.
    """
    response = llm.invoke(prompt)
    return [line.strip("1234567890. ") for line in response.content.strip().split("\n") if line.strip()]

# --- Main Page ---
def page_database_qa():
    
    for q in SUGGESTIONS:
        if st.button(q, key=q):
            st.session_state.suggested_query = q
            st.rerun()

    db = get_database()
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
    schema_info = db.get_table_info(table_names=TABLES)

    system_prompt = f"""
        You are an AI assistant designed to query a SQL Server database.
        Only use the following 4 tables:
        {schema_info}

        Rules:
        - Only generate SELECT statements.
        - Do not make up columns.
        - No INSERT, UPDATE, DELETE, or DROP.
        - If unsure, ask for clarification.
        - Stay in context. If you don't know the answer just say "I don't know".
    """

    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            input_key="input", output_key="output",
            memory_key="chat_history", return_messages=True
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    if "agent" not in st.session_state:
        st.session_state.agent = create_sql_agent(
            llm=llm,
            db=db,
            prompt=prompt,
            verbose=True,
            handle_parsing_errors=True,
            agent_type="openai-tools",
            agent_executor_kwargs={"memory": st.session_state.memory, "return_intermediate_steps": True}
        )

    messages = st.session_state.memory.chat_memory.messages
    for user_msg, ai_msg in [(messages[i].content, messages[i+1].content) for i in range(0, len(messages)-1, 2) if messages[i].type == "human"][-5:]:
        with st.chat_message("User"): st.write(user_msg)
        with st.chat_message("Assistant"): st.write(ai_msg)

    query = st.chat_input("Ask a question about your SQL data")
    if "suggested_query" in st.session_state:
        query = st.session_state.pop("suggested_query")

    if query:
        with st.chat_message("User"): st.write(query)
        try:
            result = st.session_state.agent.invoke({"input": query})
            response = result["output"]
            with st.chat_message("Assistant"): st.write(response)
            st.session_state.last_followups = generate_follow_ups(llm, query)
        except Exception as e:
            st.error(str(e))

    if "last_followups" in st.session_state:
        st.markdown("**You may also ask:**")
        for i, q in enumerate(st.session_state.last_followups):
            if st.button(q, key=f"followup_{i}"):
                st.session_state.suggested_query = q
                st.rerun()

# --- Main App ---
def main():
    st.set_page_config(page_title="Database GPT Tool", layout="wide")
    apply_custom_css_and_logo()
    page_database_qa()

if __name__ == "__main__":
    main()


