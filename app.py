"""
app.py — Conversational web interface for the Frankfurt School RAG.

Usage: uv run streamlit run app.py
"""

import config
import os
import re
from pathlib import Path

import anthropic
import chromadb
import streamlit as st
from openai import OpenAI

from query import build_prompt, embed_question, retrieve, synthesise

CHROMA_DIR = "chroma_db"
OUTPUT_DIR = Path("output")

# Short command to save the previous answer without new generation
WRITE_ONLY_RE = re.compile(
    r'^\s*(please\s+)?(write|save|output|export)\s+(this|it)\s*(out\s*)?(to\s+a?\s*file|to\s+disk|out)?\s*[\s.!]*$',
    re.IGNORECASE,
)
# Write/save intent embedded in a larger request — generate then save
WRITE_AND_GENERATE_RE = re.compile(
    r'\b(write|save|output|export)\b.{0,80}\bfile\b|\bsave\s+to\s+file\b|\bwrite\s+to\s+file\b',
    re.IGNORECASE,
)

st.title("Western Esotericism & Critical Theory")
st.caption("Exploring the connections between the Hermetic tradition, German Idealism, Marxism, and the Frankfurt School.")

with st.sidebar:
    st.header("File output")
    output_filename = st.text_input("Filename", value="output.md")
    save_clicked = st.button("Save last answer to file")

if "messages" not in st.session_state:
    st.session_state.messages = []

if save_clicked:
    last_answer = next(
        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
        None,
    )
    if last_answer:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / output_filename
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(last_answer + "\n\n---\n\n")
        st.sidebar.success(f"Saved to {out_path}")
    else:
        st.sidebar.warning("Nothing to save yet.")


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
if question := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    def append_to_file(text: str) -> str:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / output_filename
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(text + "\n\n---\n\n")
        return str(out_path)

    if WRITE_ONLY_RE.match(question):
        # Save the previous answer — no new generation needed
        last_answer = next(
            (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
            None,
        )
        if last_answer:
            out_path = append_to_file(last_answer)
            reply = f"Written to `{out_path}`."
        else:
            reply = "Nothing to write yet — ask a question first."
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

    else:
        openai_client, anthropic_client, collection = load_clients()
        with st.chat_message("assistant"):
            with st.spinner(""):
                question_vector = embed_question(question, openai_client)
                chunks = retrieve(question_vector, collection)
                prompt = build_prompt(question, chunks, history=st.session_state.messages[:-1])
                answer = synthesise(prompt, anthropic_client)
            st.markdown(answer)
            if WRITE_AND_GENERATE_RE.search(question):
                out_path = append_to_file(answer)
                st.caption(f"Written to `{out_path}`.")
        st.session_state.messages.append({"role": "assistant", "content": answer})
