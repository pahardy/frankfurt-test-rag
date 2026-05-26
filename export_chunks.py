"""
export_chunks.py — Export all stored chunks to a CSV for inspection.

Usage: uv run export_chunks.py
Opens as a spreadsheet in Excel or Numbers.
"""

import config
import csv
import chromadb
from pathlib import Path

OUTPUT = Path("chunks_export.csv")
CHROMA_DIR = Path("chroma_db")


def export():
    col = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_collection("frankfurt")
    result = col.get(include=["documents", "metadatas", "embeddings"])

    rows = sorted(
        zip(result["ids"], result["metadatas"], result["documents"], result["embeddings"]),
        key=lambda r: (r[1]["source"], r[1]["chunk_index"]),
    )

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "source", "chunk_index", "text", "vector (1536 numbers)"])
        for id_, meta, doc, vec in rows:
            rounded = [round(n, 6) for n in vec]
            writer.writerow([id_, meta["source"], meta["chunk_index"], doc, rounded])

    print(f"Exported {len(rows)} chunks to {OUTPUT}")


if __name__ == "__main__":
    export()
