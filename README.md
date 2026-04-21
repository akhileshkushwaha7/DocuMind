# DocuMind

Chat with your PDF documents using AI. Upload a PDF, ask questions, get answers streamed back in real time — powered by semantic search and GPT-4o-mini.

![Stack](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square) ![Stack](https://img.shields.io/badge/Next.js-14-black?style=flat-square) ![Stack](https://img.shields.io/badge/Qdrant-vector_db-red?style=flat-square) ![Stack](https://img.shields.io/badge/Docker-compose-2496ED?style=flat-square)

---

## What it does

- Upload a PDF → it gets chunked, embedded, and indexed automatically
- Ask questions in a chat interface → answers stream back token by token
- Conversation history is preserved across sessions
- Admin panel shows platform stats, user table, and upload analytics

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.11) |
| Frontend | Next.js 14, Tailwind CSS |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| Cache / Queue | Redis 7 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | OpenAI GPT-4o-mini |
| Task worker | arq (async Redis queue) |
| ORM | SQLAlchemy 2 + Alembic |
| Auth | JWT (access + refresh tokens) |
| Containers | Docker Compose |

---


## Getting started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Node.js 20+
- Python 3.11+ (for local dev only — not needed if running fully in Docker)
- An OpenAI API key

### 1. Clone and configure

```bash
git clone https://github.com/yourname/documind.git
cd documind
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://documind:documind@postgres:5432/documind
SYNC_DATABASE_URL=postgresql://documind:documind@postgres:5432/documind
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY=sk-...
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Start the backend stack

```bash
docker compose up --build
```

This starts 5 services: `postgres`, `redis`, `qdrant`, `api`, `worker`.

Verify everything is healthy:

```bash
docker compose ps
```

### 3. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## How the embedding pipeline works

```
PDF upload
    │
    ▼
Save file to disk + metadata to Postgres (status: pending)
    │
    ▼
Enqueue job → Redis queue
    │
    ▼
arq worker picks up job
    │
    ├── Extract text          (PyMuPDF)
    ├── Chunk into 500 tokens (tiktoken, 50-token overlap)
    ├── Embed each chunk      (all-MiniLM-L6-v2, 384 dimensions)
    └── Upsert vectors        (Qdrant collection: "documents")
    │
    ▼
Update document status → ready
```

## How the RAG chat pipeline works

```
User sends message
    │
    ▼
Embed query locally (all-MiniLM-L6-v2)
    │
    ▼
Search Qdrant → top 5 matching chunks (filtered by document_id)
    │
    ▼
Build prompt: system + chunks as context + conversation history
    │
    ▼
Stream response from GPT-4o-mini via OpenAI API
    │
    ▼
SSE stream → browser renders tokens in real time
    │
    ▼
Save complete message pair to Postgres
```

---

## API reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user |

### Documents

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents/upload` | Upload a PDF |
| GET | `/documents/` | List user's documents (paginated) |
| GET | `/documents/{id}` | Get document detail (cached) |
| GET | `/documents/{id}/status` | Poll embedding status |
| DELETE | `/documents/{id}` | Delete document |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/{doc_id}` | Send message, stream SSE response |
| GET | `/chat/{doc_id}/history` | Get conversation history |

### Admin (admin role required)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/users` | List all users with doc counts |
| GET | `/admin/stats` | Platform totals + uploads per day |

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async Postgres URL | — |
| `SYNC_DATABASE_URL` | Sync Postgres URL (Alembic) | — |
| `REDIS_URL` | Redis connection URL | — |
| `QDRANT_URL` | Qdrant HTTP URL | — |
| `JWT_SECRET` | Secret key for signing JWTs | — |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `OPENAI_API_KEY` | OpenAI API key | — |

---

## Making a user admin

```bash
docker exec -it documind-postgres-1 psql -U documind
```

```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

Admin users see an **Admin** link in the navbar that opens the platform dashboard.

---

## Rate limiting

Chat endpoint is limited to **20 requests per user per minute** using a Redis sliding window counter. Exceeding the limit returns:

```json
{ "detail": "Too many requests. Try again in 42 seconds." }
```

---

## Development tips

**Watch backend logs:**
```bash
docker compose logs api --follow
```

**Watch worker logs:**
```bash
docker compose logs worker --follow
```

**Rebuild after dependency changes:**
```bash
docker compose build --no-cache
docker compose up
```

**Run a new migration:**
```bash
# After editing a model
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head
```

**Connect to Postgres directly:**
```bash
docker exec -it documind-postgres-1 psql -U documind
```

**Inspect Qdrant collections:**

Open [http://localhost:6333/dashboard](http://localhost:6333/dashboard) in your browser.

---

## Known limitations

- Only PDF files are supported for upload
- Embedding runs on CPU — large PDFs (100+ pages) may take 30–60 seconds
- One conversation per document per user (no multiple chat threads)
- No file size limit enforced on the server — add one for production use

---

## License

MIT
