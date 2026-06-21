"""
query.py — Embed a question, retrieve relevant chunks, and synthesize an answer with Claude.

Usage: uv run query.py
"""

import config
import os
from pathlib import Path

import anthropic
import chromadb
from openai import OpenAI

CHROMA_DIR = Path("chroma_db")
EMBED_MODEL = "text-embedding-3-small"
CLAUDE_MODEL = "claude-sonnet-4-6"
TOP_K = 5


def embed_question(question: str, client: OpenAI) -> list[float]:
    """Convert the question to a vector using the same model as the stored chunks."""
    return client.embeddings.create(input=question, model=EMBED_MODEL).data[0].embedding


def retrieve(question_vector: list[float], collection) -> list[dict]:
    """Find the TOP_K most similar chunks in ChromaDB."""
    results = collection.query(
        query_embeddings=[question_vector],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "similarity": round(1 - dist, 4),
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def build_prompt(question: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    """Assemble the passages, optional conversation history, and question into a prompt."""
    passages = "\n\n".join(f'"{c["text"]}"' for c in chunks)

    history_section = ""
    if history:
        turns = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history[-6:]  # last 3 exchanges
        )
        history_section = f"\nConversation so far:\n{turns}\n"

    return f"""You are a knowledgeable conversation partner with deep expertise across the Western \
esoteric and philosophical tradition. Your knowledge spans the classical Hermetic corpus, \
Renaissance occultism and alchemy (Paracelsus, Böhme, the Rosicrucians), German Idealism \
(Hegel), Marxist theory (Marx, Lukács), and Frankfurt School critical theory (Adorno, \
Benjamin, Habermas, Horkheimer, Marcuse). The purpose of this conversation is to explore \
the connections, relationships, and contrasts between these traditions — how esoteric and \
mystical thought relates to, anticipates, diverges from, or is transformed by the great \
currents of modern philosophy and critical theory. Answer naturally and directly, as if \
speaking with someone genuinely curious about these ideas and their intersections. Do not \
reference passage numbers or mention that you are working from provided texts — just answer \
engagingly and in your own voice. If asked to write something out or produce a piece of text, \
simply write it in full — file saving is handled externally by the application.

The following passages are provided as context — draw on them where relevant, but answer from your full knowledge of these traditions:{history_section}

{passages}

Question: {question}"""


def synthesise(prompt: str, client: anthropic.Anthropic) -> str:
    """Send the prompt to Claude and return its response."""
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def query(question: str) -> tuple[str, list[dict]]:
    """Full pipeline: embed → retrieve → synthesise. Importable by app.py."""
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection("frankfurt")

    question_vector = embed_question(question, openai_client)
    chunks = retrieve(question_vector, collection)
    prompt = build_prompt(question, chunks)
    answer = synthesise(prompt, anthropic_client)
    return answer, chunks


if __name__ == "__main__":
    print("Frankfurt School RAG — type your question, or 'quit' to exit.\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        print("\nSearching and synthesising...\n")
        answer, chunks = query(question)

        print(f"Answer:\n{answer}")
        print("\nSources used:")
        for c in chunks:
            print(f"  {c['source']}  chunk {c['chunk_index']}  (similarity {c['similarity']})")
        print()
