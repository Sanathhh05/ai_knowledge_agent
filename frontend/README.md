# AI Knowledge Assistant

A full-stack RAG (Retrieval-Augmented Generation) application allowing users to upload documents (PDF, DOCX, TXT), ingest web URLs and YouTube videos, and chat with their knowledge base using local open-weight AI models.

## Phase 4 RAG Architecture

The application uses an entirely local AI pipeline for data privacy and avoiding API costs:

```text
User Query
 ↓
bge-m3 (Local Embedding via Ollama)
 ↓
pgvector (PostgreSQL Vector Search)
 ↓
Top-K Chunks
 ↓
Context Builder (RAG Service)
 ↓
Qwen3 8B (Local LLM via Ollama)
 ↓
Answer
 ↓
Citations (Source Metadata)
```

### Key Technologies
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Next.js (React), Vanilla CSS
- **Vector DB**: `pgvector` inside PostgreSQL. Chosen for seamless integration with existing relational data (users, sources, conversations) ensuring ACID compliance and easy user isolation.
- **Embeddings**: `bge-m3` (1024 dims). Excellent multilingual support and retrieval performance.
- **LLM**: `qwen3:8b`. Hits the sweet spot for performance on consumer GPUs (fits in ~6GB VRAM) while strictly following RAG system instructions.

### Features
- **User Isolation**: All vector searches and source interactions are strictly scoped to the authenticated user's ID. You cannot query or retrieve another user's chunks.
- **Chat History**: Conversations and individual messages are persisted in PostgreSQL. The `rag_service.py` fetches the last 8 messages of history and passes them to the LLM distinctly from the source context to enable conversational memory.
- **Citations**: LLM responses include exact citations derived directly from the vector search results, not hallucinated by the model. 
- **Hallucination Handling**: The LLM prompt is strictly constrained. If a query's answer is not within the retrieved top-K chunks, the AI will gracefully state it cannot find the information rather than guessing.

## Setup & Running

1. **Start PostgreSQL**: Make sure PostgreSQL is running with the `pgvector` extension installed.
2. **Start Ollama**: Have Ollama running locally.
3. **Download Models**: `ollama pull bge-m3:latest` and `ollama pull qwen3:8b`
4. **Backend**: 
   ```bash
   cd backend
   .\venv\Scripts\activate
   uvicorn app.main:app --reload
   ```
5. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
