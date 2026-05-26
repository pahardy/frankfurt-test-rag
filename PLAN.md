# Build Plan: Frankfurt School RAG

This document walks through every step of what we're building and why. Read it as a companion to the code — each section explains the concept before the implementation.

---

## Phase 1: Setup

**What we're doing:** Installing the tools the project depends on and organizing the folder structure.

**Why:** Python projects declare their dependencies in a file (`pyproject.toml`). The `uv` package manager reads that file and installs everything into an isolated environment so it doesn't interfere with anything else on your machine.

**Dependencies we'll install:**
- `openai` — the Python library for calling OpenAI's embedding API
- `anthropic` — the Python library for calling Claude
- `chromadb` — the local vector database
- `streamlit` — turns a Python file into a web app
- `python-dotenv` — reads your `.env` file so scripts can access your API keys

**Result:** A working Python environment and a clean folder structure ready for the next phases.

---

## Phase 2: Ingestion (`ingest.py`)

This is the most important phase to understand conceptually. It's run once (and re-run whenever you add new texts).

### Step 2a: Read the text files

**What:** The script reads your `.txt` files from the `texts/` folder.

**Why:** We need raw text before we can do anything else. PDFs are binary files; plain text is what the rest of the pipeline works with. (Your `.txt` files are already ready.)

---

### Step 2b: Chunk the text

**What:** Each text file is split into overlapping passages of roughly 500 words each, with a small overlap between adjacent chunks (e.g. the last 50 words of chunk 1 are repeated at the start of chunk 2).

**Why:** Language models have a limit on how much text they can process at once. More importantly, when someone asks a question, you don't want to retrieve an entire book — you want the specific passage that's relevant. Smaller chunks make retrieval more precise.

The overlap prevents a relevant idea from being cut in half at a chunk boundary.

**Example:** A 10,000-word essay becomes roughly 20 chunks of ~500 words each.

---

### Step 2c: Embed each chunk

**What:** Each chunk of text is sent to OpenAI's embedding API (`text-embedding-3-small`). The API returns a list of ~1,500 numbers — a vector.

**Why:** This is the core idea behind semantic search. An embedding converts meaning into geometry. Two passages that discuss the same idea will have vectors that point in similar directions in this high-dimensional space, even if they use different words. This is what allows the system to find relevant passages when someone asks a question in their own words.

Think of it as: the model has read so much text that it can locate any passage on a kind of "map of meaning." Similar ideas end up near each other on that map.

---

### Step 2d: Store in ChromaDB

**What:** Each chunk's vector (plus the original text and metadata like filename and chunk number) is saved to ChromaDB, which writes it to a local folder called `chroma_db/`.

**Why:** We need to persist these vectors so we don't have to re-embed everything every time someone asks a question. ChromaDB stores them efficiently and provides fast search.

**What's stored for each chunk:**
- The vector (list of numbers representing meaning)
- The original text (so we can show it to the user)
- Metadata: which file it came from, which chunk number it is

**Result:** A `chroma_db/` folder on your machine containing all the embedded knowledge from your texts.

---

## Phase 3: Querying (`query.py`)

This runs every time someone asks a question. It's fast — no re-processing of documents.

### Step 3a: Embed the question

**What:** The user's question is sent to OpenAI's same embedding model, which returns a vector for it.

**Why:** To find relevant passages, we need the question to live in the same "map of meaning" as the document chunks. The same model that embedded the documents embeds the question, so they're comparable.

---

### Step 3b: Search ChromaDB

**What:** ChromaDB compares the question's vector against all stored chunk vectors and returns the top 5 most similar ones.

**Why:** This is semantic search — not keyword matching, but meaning matching. A question like "What does Adorno say about mass culture?" will find chunks about the culture industry even if they don't use those exact words.

The similarity measure is called cosine similarity: it measures the angle between two vectors. A small angle means the ideas are close; a large angle means they're unrelated.

---

### Step 3c: Synthesize an answer with Claude

**What:** The top 5 retrieved chunks are assembled into a prompt along with the original question, and sent to Claude. Claude reads the passages and writes a grounded answer.

**Why:** Retrieval alone gives you relevant text fragments. Claude's job is to synthesize them into a coherent, readable answer — explaining connections, resolving tensions between passages, and acknowledging when the retrieved text doesn't fully address the question.

The prompt tells Claude: "Answer only using the provided passages. If the answer isn't in the passages, say so." This keeps responses grounded in the source material rather than Claude's general knowledge — which is the whole point of RAG.

---

### Step 3d: Return the answer with sources

**What:** The answer is returned alongside the source passages that were used to generate it.

**Why:** Transparency. You can verify that Claude's answer is actually grounded in the texts, and see exactly which passages it drew from. This is especially important for philosophical content where the exact wording matters.

---

## Phase 4: Web Interface (`app.py`)

**What:** A Streamlit web app with a text input box. The user types a question, hits Enter, and sees Claude's answer plus the source passages below it.

**Why:** Others need to use this without running Python commands. Streamlit turns a plain Python file into a web page that anyone can open in a browser. You run it once on your machine (or later deploy it to a free host), and it handles the rest.

**What the interface will show:**
- A question input box
- Claude's synthesized answer
- The source passages retrieved from ChromaDB, with filename and chunk number

---

## Build sequence

We'll build in this order, validating each step before moving to the next:

1. **Setup** — install dependencies, organize folders, verify API keys work
2. **Ingest** — run `ingest.py` on your two `.txt` files, confirm chunks are stored in ChromaDB
3. **Query** — run `query.py` from the command line with a test question, confirm retrieval and Claude's answer look right
4. **App** — build `app.py`, run it locally, confirm the web interface works end to end

At each step I'll show you what's happening and we'll verify it before proceeding.
