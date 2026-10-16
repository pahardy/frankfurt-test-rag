"""
ingest.py — Read text files, chunk them, embed them, and store in ChromaDB.

Run once to populate the database, then re-run whenever you add new texts.
Usage: uv run ingest.py
"""

import config  # loads .env and SSL certs
import os
import time
from pathlib import Path

import chromadb
from openai import OpenAI

TEXTS_DIR = Path("texts")
CHROMA_DIR = Path("chroma_db")
EMBED_MODEL = "text-embedding-3-large"
CHUNK_WORDS = 400
OVERLAP_WORDS = 50
BATCH_SIZE = 100  # number of chunks to embed in one API call


def load_texts() -> dict[str, str]:
    """Read all .txt files from the texts/ directory."""
    texts = {}
    for path in sorted(TEXTS_DIR.glob("*.txt")):
        content = path.read_text(encoding="utf-8")
        texts[path.stem] = content
        print(f"Loaded: {path.name}  ({len(content.split()):,} words)")
    return texts


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += CHUNK_WORDS - OVERLAP_WORDS
    return chunks


def embed_batch(texts: list[str], client: OpenAI) -> list[list[float]]:
    """Send a batch of texts to OpenAI and return their embedding vectors."""
    # ~30k chars ≈ 7500 tokens — safely under the 8192-token API limit.
    # Guards against binary artifacts or unusually long paragraphs in source files.
    safe = [t[:30_000] for t in texts]
    for attempt in range(5):
        try:
            response = client.embeddings.create(input=safe, model=EMBED_MODEL)
            return [item.embedding for item in response.data]
        except Exception as e:
            if attempt < 4:
                wait = 10 * (attempt + 1)
                print(f"    Error (attempt {attempt + 1}/5) — waiting {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def ingest():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("frankfurt")

    texts = load_texts()
    if not texts:
        print("No .txt files found in texts/. Nothing to ingest.")
        return

    for doc_name, text in texts.items():
        chunks = chunk_text(text)
        print(f"\n{doc_name}: {len(chunks)} chunks — embedding and storing...")

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            vectors = embed_batch(batch, openai_client)

            ids = [f"{doc_name}__chunk_{i + j}" for j in range(len(batch))]
            metadatas = [{"source": doc_name, "chunk_index": i + j} for j in range(len(batch))]

            # upsert = insert or update, so re-running is safe
            collection.upsert(ids=ids, embeddings=vectors, documents=batch, metadatas=metadatas)
            print(f"  Stored chunks {i}–{i + len(batch) - 1}")

    print(f"\nDone. Total chunks in database: {collection.count()}")


if __name__ == "__main__":
    ingest()
