# Counter-Proposal: Frankfurt School RAG

## The original stack and why I'd change it

The original proposal used **n8n + Supabase**. Both are solid production tools, but they're mismatched to this project at this stage:

- **n8n** is a GUI workflow orchestrator built for production automation — scheduling, retries, monitoring across many connected services. For a RAG pipeline that runs on demand, it adds complexity without adding value. The pipeline itself is only 2 steps (ingest documents, answer questions), and those are much easier to understand as plain code than as a visual node graph.
- **Supabase** is a hosted Postgres database. It works for vector storage via its pgvector extension, but it requires account setup, connection strings, and a running cloud service. For a small corpus starting with a few essays, this is infrastructure you don't need yet.

The goal is to learn AI concepts hands-on. You want to see the pipeline, not be abstracted away from it.

---

## Proposed stack

| Role | Tool | Why |
|------|------|-----|
| Embeddings | OpenAI (`text-embedding-3-small`) | Already in your setup; reliable; cheaper than `large` with minimal quality difference |
| Vector storage | **ChromaDB** (local) | Zero infrastructure — stores as a folder on your machine; simple Python API; easy to inspect |
| LLM synthesis | **Claude** (Anthropic) | Better than GPT-4 for analytical/philosophical content; you're already in the Claude ecosystem |
| Web interface | **Streamlit** | One Python file gives you a proper web app others can use; no frontend knowledge needed |
| Orchestration | **None (plain Python)** | 3 small scripts replace n8n entirely; each step is readable |

---

## How the pipeline works

### Ingestion (run once, or when you add new texts)

```
Text files → chunk into passages → embed each passage → store in ChromaDB
```

One script (`ingest.py`) does this. You point it at your text files, it processes them, and saves everything to a local `chroma_db/` folder.

### Querying (run on demand)

```
User question → embed the question → find similar passages in ChromaDB → send passages + question to Claude → return answer
```

One script (`query.py`) does this, or it runs inside the Streamlit app.

### Web app

```
app.py  →  text input box  →  runs the query pipeline  →  shows the answer + source passages
```

Streamlit turns `app.py` into a web page. Others can open it in a browser and ask questions.

---

## Project structure

```
frankfurt-test-rag/
├── texts/                        # your source .txt files
├── chroma_db/                    # auto-created; holds the vector database
├── ingest.py                     # chunk, embed, and store texts
├── query.py                      # retrieve and synthesize answers
├── app.py                        # Streamlit web interface
├── .env                          # API keys (never committed to git)
└── pyproject.toml                # dependencies (managed by uv)
```

---

## What you'll need

- **OpenAI API key** — for embeddings (already in your `.env.example`)
- **Anthropic API key** — for Claude (you have one via Claude Code)
- That's it. No Supabase account, no n8n account, no cloud services.

---

## Migration path (when you're ready to scale)

Nothing about this stack is a dead end:

- **More texts / books**: ChromaDB handles tens of thousands of chunks comfortably. Scaling to full books changes nothing about the code.
- **Hosted database**: If you want others to query without running the app locally, ChromaDB can be swapped for Supabase pgvector (or Pinecone) with a small change to one file.
- **Shared deployment**: The Streamlit app can be deployed to Streamlit Community Cloud for free, giving others a public URL.

---

## Recommendation

Start here. The stack is simple, cheap to run, and — importantly — every step is visible to you as the person learning. Once you've ingested your first corpus and run your first query, you'll have a clear mental model of what RAG actually does. That's the point of the project.
