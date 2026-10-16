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
EMBED_MODEL = "text-embedding-3-large"
CLAUDE_MODEL = "claude-sonnet-4-6"
TOP_K = 5

SYSTEM_PROMPT = (
    "You are a knowledgeable conversation partner with deep expertise across the Western "
    "esoteric and philosophical tradition. Your knowledge spans the classical Hermetic corpus, "
    "Renaissance occultism and alchemy (Paracelsus, Böhme, the Rosicrucians), German Idealism "
    "(Hegel), Marxist theory (Marx, Lukács), and Frankfurt School critical theory (Adorno, "
    "Benjamin, Habermas, Horkheimer, Marcuse). The purpose of this conversation is to explore "
    "the connections, relationships, and contrasts between these traditions — how esoteric and "
    "mystical thought relates to, anticipates, diverges from, or is transformed by the great "
    "currents of modern philosophy and critical theory. Answer naturally and directly, as if "
    "speaking with someone genuinely curious about these ideas and their intersections. Do not "
    "reference passage numbers or mention that you are working from provided texts — just answer "
    "engagingly and in your own voice."
)


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


def synthesise(
    question: str,
    chunks: list[dict],
    history: list[dict],
    client: anthropic.Anthropic,
) -> str:
    """Call Claude with full multi-turn conversation history and RAG context."""
    passages = "\n\n".join(f'"{c["text"]}"' for c in chunks)
    user_message = (
        "The following passages from the corpus are relevant — draw on them where helpful:\n\n"
        + passages
        + "\n\n"
        + question
    )
    # Build the messages array: prior turns (up to last 6 messages = 3 exchanges) + current question
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-6:]]
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


if __name__ == "__main__":
    print("Frankfurt School RAG — type your question, or 'quit' to exit.\n")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection("frankfurt")
    history: list[dict] = []

    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        print("\nSearching and synthesising...\n")
        question_vector = embed_question(question, openai_client)
        chunks = retrieve(question_vector, collection)
        answer = synthesise(question, chunks, history, anthropic_client)

        print(f"Answer:\n{answer}")
        print("\nSources used:")
        for c in chunks:
            print(f"  {c['source']}  chunk {c['chunk_index']}  (similarity {c['similarity']})")
        print()

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
