# Philosophy RAG

A conversational retrieval-augmented generation system grounded in Western philosophy — from the classical Hermetic tradition through Marx, Hegel, and the Frankfurt School.

## Motivation

This project has two purposes running in parallel.

The first is personal: an interest in the long tradition of Western esoteric and critical thought — the alchemists, the Hermetic texts, the idealist philosophers, and the Frankfurt School theorists who inherited and transformed all of it. The corpus was assembled to make that terrain explorable through conversation rather than reading in isolation.

The second is technical: a working ground for learning how retrieval-augmented generation actually operates. Rather than using a toy dataset, the project is built on a real corpus of philosophical texts — dense, interconnected, and demanding enough to make the quality of the retrieval pipeline matter. The goal is to understand how chunking strategies, embedding models, similarity search, and LLM synthesis interact in practice, using Claude as the primary AI partner throughout.

The two motivations reinforce each other: the subject matter is rich enough to stress-test the RAG pipeline, and the RAG pipeline makes the subject matter more accessible.

## Corpus

~10,550 chunks across 63 texts including:

- **Karl Marx** — Capital Vol. 1, Grundrisse, Economic & Philosophic Manuscripts, German Ideology, Communist Manifesto, Theses on Feuerbach
- **Frankfurt School** — Adorno, Benjamin, Habermas, Horkheimer, Lukács, Marcuse
- **Sigmund Freud** — Civilization and Its Discontents, Beyond the Pleasure Principle, Group Psychology and the Analysis of the Ego, Totem and Taboo, Three Essays on the Theory of Sexuality, The Future of an Illusion
- **Hegel** — Phenomenology of Spirit, Science of Logic, Philosophy of Right, Philosophy of History, Philosophy of Mind, Shorter Logic
- **Jakob Böhme** — Signature of All Things, Confessions
- **Paracelsus** — Aurora of the Philosophers, Coelum Philosophorum, Tincture of the Philosophers, Treasure of Treasures, Of the Nature of Things
- **Hermetic texts** — Corpus Hermeticum, Mead's Thrice-Greatest Hermes (3 vols), Asclepius, Emerald Tablet, Golden Tractate
- **Rosicrucian manifestos** — Fama, Confessio, Chemical Wedding

## Setup

```bash
# Install dependencies
uv sync

# Copy and fill in credentials
cp .env.example .env
```

Required keys in `.env`:
- `OPENAI_API_KEY` — for text embeddings (`text-embedding-3-large`)
- `ANTHROPIC_API_KEY` — for answer synthesis (Claude)

If you're behind a corporate SSL proxy, export your system certificates to a `.pem` file and set `SSL_CERT_FILE=/path/to/certs.pem` in `.env`.

## Usage

```bash
# 1. Scrape source texts (skips files already in texts/)
uv run scrape.py

# 2. Embed and store in ChromaDB (safe to re-run — uses upsert)
uv run ingest.py

# 3. Run the web interface
uv run streamlit run app.py

# Or query from the command line
uv run query.py
```

## Adding texts

Add entries to the `TEXTS` dict in `scrape.py`, then re-run `scrape.py` and `ingest.py`. Three formats are supported:

```python
# Single page
"name": "https://example.com/page.htm"

# Multiple explicit pages
"name": {"pages": ["https://...", "https://..."]}

# Auto-discover chapters from an index page
"name": {"index": "https://example.com/index.htm"}
```

PDFs can be placed directly in `texts/` as `.txt` files (extract text first).

## Architecture

```
scrape.py  →  texts/*.txt  →  ingest.py  →  chroma_db/
                                                 ↓
                              query.py / app.py (RAG pipeline)
```

- **Chunking** — 400 words, 50-word overlap
- **Embeddings** — OpenAI `text-embedding-3-large` (3072 dimensions)
- **Vector store** — ChromaDB (local, persistent)
- **Synthesis** — Anthropic Claude
