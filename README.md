# Philosophy RAG

A conversational retrieval-augmented generation system grounded in Western philosophy — from the classical Hermetic tradition through Marx, Hegel, and the Frankfurt School.

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
- `OPENAI_API_KEY` — for text embeddings (`text-embedding-3-small`)
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
- **Embeddings** — OpenAI `text-embedding-3-small` (1536 dimensions)
- **Vector store** — ChromaDB (local, persistent)
- **Synthesis** — Anthropic Claude
