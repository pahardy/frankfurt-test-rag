"""
app.py — Conversational web interface for the Frankfurt School RAG.

Usage: uv run streamlit run app.py
"""

import config
import os

import anthropic
import chromadb
import streamlit as st
from openai import OpenAI

from query import build_prompt, embed_question, retrieve, synthesise

CHROMA_DIR = "chroma_db"

st.title("Frankfurt School")
st.caption("A conversation grounded in critical theory texts.")

if "messages" not in st.session_state:
    st.session_state.messages = []


@st.cache_resource
def load_clients():
    """Create API clients and open the database once at startup, reuse across requests."""
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    collection = chromadb.PersistentClient(path=CHROMA_DIR).get_collection("frankfurt")
    return openai_client, anthropic_client, collection


# Render conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input sits at the bottom of the page
if question := st.chat_input("Ask something about Frankfurt School critical theory..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    openai_client, anthropic_client, collection = load_clients()

    with st.chat_message("assistant"):
        with st.spinner(""):
            question_vector = embed_question(question, openai_client)
            chunks = retrieve(question_vector, collection)
            prompt = build_prompt(question, chunks, history=st.session_state.messages[:-1])
            answer = synthesise(prompt, anthropic_client)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
