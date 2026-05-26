# Philosophy RAG Project

This project is meant to bring together 2 interests: 1) a desire to learn AI concepts and get some hands on work with it, 2) and some esoteric philosophical concepts. The ultimate aim of the project is to create a vector database built on essays from the Frankfurt School, and use that as RAG to answer questions and provide content about it.


## Steps

I believe this will require the following steps:

1. Take a corpus (a book, philosopher’s collected works, commentary, etc.)
2. Break it into chunks
3. Convert chunks into embeddings (vector representations)
4. Store them in a vector database
5. Retrieve relevant chunks during questioning
6. Use an LLM to synthesize answers from retrieved material

### High-level project outline

- Corpus selection: begin with Frankfurt School texts and add more sources over time.
- Text preparation: split documents into chunks, clean the text, and normalize formatting.
- Embeddings: convert chunks into vector representations using an embeddings model or service.
- Vector storage: store embeddings plus metadata in a vector database.
- Retrieval: perform semantic search to find relevant chunks for a user question.
- Answer synthesis: use retrieved chunks to generate grounded responses with an LLM.

I don't have a background in development.  Your role will be to not only design and develop the app, but to act as a partner in that process, letting me know what's going on. 


## Tools

Currently the following is available to assist and will be used to carry out the project:

- n8n — workflow/orchestration
- Google Drive — source document storage
- Supabase — vector DB / embeddings storage

### Questions to answer as we go

- Embeddings model/service — which embedding provider or model will be used?
- LLM provider — OpenAI, Anthropic, local model, or another?
- Runtime / integration language — Python, Node.js, or another environment for the ingestion/retrieval app?
- Vector search query layer — will we use Supabase's vector search directly or add a search wrapper? 
