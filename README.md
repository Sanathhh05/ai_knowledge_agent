# RAMBO — Your AI Knowledge Assistant

RAMBO is a full-stack, AI-powered knowledge management system. It allows users to upload documents (PDF, DOCX, TXT), add web links, and ingest YouTube videos. Users can query their personal, isolated knowledge base through a modern chat interface using state-of-the-art Retrieval-Augmented Generation (RAG) and voice interaction.

---

## Features

- **Authentication**: Secure email/password login with JWT and bcrypt hashing. Strict user data isolation.
- **Source Ingestion**: Upload PDFs, DOCX, TXT files, YouTube URLs, and Web articles.
- **RAG & Chat**: Have a multi-turn conversation with your documents. Every answer includes citations linking directly to the primary source.
- **Voice Interaction**: Talk to your sources! Click the microphone to ask questions using your voice, and listen to the AI's responses via Text-to-Speech (TTS).
- **100% Local AI Stack**: No OpenAI keys required. Embeddings, Generative AI, and Speech-to-Text all run locally for maximum privacy and cost-efficiency.

---

## Architecture & Tech Stack

### Frontend
- **Framework**: Next.js 16 + React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS (Custom Dark Navy & Amber "RAMBO" theme)
- **Voice**: Browser `MediaRecorder` API and `SpeechSynthesis` API

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Database ORM**: SQLAlchemy 2.x
- **Database**: PostgreSQL 18
- **Vector Search**: `pgvector` (PostgreSQL extension)

### Local AI & RAG Pipeline
- **Generative LLM**: `qwen3:8b` via Ollama
- **Embedding Model**: `bge-m3:latest` via Ollama (1024 dimensions)
- **Speech-to-Text (STT)**: `faster-whisper` (CPU/int8 optimized)

---

## System Workflow

1. **Ingestion**: A user uploads a file. The text is extracted, normalized, and chunked.
2. **Embedding**: Chunks are passed to `bge-m3` via Ollama. The resulting 1024-dimension vectors are saved in PostgreSQL using `pgvector`.
3. **Voice Input (Optional)**: If the user speaks, the audio is sent to the backend and transcribed via `faster-whisper`.
4. **Vector Search**: The user's query (text or transcribed audio) is embedded. A cosine similarity search (`<=>`) is performed in `pgvector`. **Security**: The search is strictly scoped to `user_id = current_user.id` to prevent data leakage.
5. **Generation**: The retrieved context chunks and conversation history are sent to `qwen3:8b`. The LLM synthesizes an answer based *only* on the provided context.
6. **Voice Output (Optional)**: The browser reads the response aloud using TTS.

---

## Setup Instructions

### 1. PostgreSQL & pgvector Setup

1. Install PostgreSQL 18.
2. Create the database:
   ```sql
   CREATE DATABASE ai_knowledge_assistant;
   ```
3. Install the `pgvector` extension for your OS. Connect to the database and enable it:
   ```sql
   \c ai_knowledge_assistant
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### 2. Ollama Setup

1. Install [Ollama](https://ollama.com/).
2. Pull the required models:
   ```bash
   ollama pull qwen3:8b
   ollama pull bge-m3:latest
   ```
3. Ensure the Ollama server is running (defaults to `http://localhost:11434`).

### 3. Backend Setup

1. Navigate to the backend directory and activate your virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ai_knowledge_assistant
   JWT_SECRET_KEY=your_secure_random_string_here
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
   OLLAMA_BASE_URL=http://localhost:11434
   FRONTEND_URL=http://localhost:3000
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### 4. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:3000`.

---

## Known Limitations & Deployment Considerations

- **Hardware Requirements**: Running `qwen3:8b`, `bge-m3`, and `faster-whisper` simultaneously requires significant RAM (at least 16GB, preferably 32GB) or a dedicated GPU with sufficient VRAM for acceptable generation speeds.
- **Deployment**:
  - The frontend can be easily deployed to Vercel.
  - The backend requires a VPS or containerized environment (e.g., Render, Railway, AWS EC2) capable of running Python and ideally providing GPU access for Ollama.
  - PostgreSQL hosting (e.g., Supabase, Neon) must support the `pgvector` extension.
- **Authentication**: RAMBO uses local Email/Password authentication. Google OAuth is not implemented.
