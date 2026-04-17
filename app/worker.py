import asyncio
import structlog
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
import uuid
log = structlog.get_logger()

# def get_redis_settings() -> RedisSettings:
#     # arq needs host/port separately, not a URL
#     return RedisSettings(host="localhost", port=6379)

import os 

def get_redis_settings() -> RedisSettings:
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    # parse redis://host:port
    host = url.split("//")[1].split(":")[0]
    port = int(url.split(":")[-1])
    return RedisSettings(host=host, port=port)
# ── Job functions ──────────────────────────────────────────────

async def embed_document(ctx, document_id: str):
    """Main embedding job — runs inside the arq worker process."""
    import fitz  # PyMuPDF
    import tiktoken
    from openai import AsyncOpenAI
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.models.document import Document, DocumentStatus
    from app.core.config import settings as cfg

    log.info("embed_job_started", document_id=document_id)

    engine = create_async_engine(cfg.DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    # openai = AsyncOpenAI(api_key=cfg.OPENAI_API_KEY)
    qdrant = QdrantClient(url=cfg.QDRANT_URL)

    async with Session() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            log.error("document_not_found", document_id=document_id)
            return

        # Mark as processing
        doc.status = DocumentStatus.processing
        await db.commit()

        try:
            # 1. Extract text from PDF
            pdf = fitz.open(doc.file_path)
            full_text = "\n".join(page.get_text() for page in pdf)
            pdf.close()

            # 2. Chunk into ~500 tokens with 50-token overlap
            enc = tiktoken.get_encoding("cl100k_base")
            tokens = enc.encode(full_text)
            chunk_size, overlap = 500, 50
            chunks = []
            start = 0
            while start < len(tokens):
                chunk_tokens = tokens[start:start + chunk_size]
                chunks.append(enc.decode(chunk_tokens))
                start += chunk_size - overlap

            # 3. Embed all chunks via OpenAI
            # response = await openai.embeddings.create(
            #     model="text-embedding-3-small",
            #     input=chunks
            # )
            # vectors = [item.embedding for item in response.data]
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            vectors = model.encode(chunks).tolist()

            # 4. Upsert into Qdrant
            collection = "documents"
            existing = [c.name for c in qdrant.get_collections().collections]
            if collection not in existing:
                qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )

            points = [
                PointStruct(
                    # id=f"{document_id}_{i}",
                    id=str(uuid.uuid5(uuid.UUID(document_id), str(i))),
                    vector=vectors[i],
                    payload={"document_id": document_id, "chunk_index": i, "text": chunks[i]}
                )
                for i in range(len(chunks))
            ]
            qdrant.upsert(collection_name=collection, points=points)

            # 5. Mark as ready
            doc.status = DocumentStatus.ready
            await db.commit()
            log.info("embed_job_done", document_id=document_id, chunks=len(chunks))

        except Exception as e:
            doc.status = DocumentStatus.failed
            await db.commit()
            log.error("embed_job_failed", document_id=document_id, error=str(e))

    await engine.dispose()
async def run_pending_documents():
    """
    Cron job entrypoint — processes all pending documents
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.models.document import Document, DocumentStatus
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(
            select(Document).where(Document.status == DocumentStatus.processing)
        )

        docs = result.scalars().all()

        for doc in docs:
            print(f"[CRON] Processing document {doc.id}")
            await embed_document(None, str(doc.id))

    await engine.dispose()


# ── Worker class config ────────────────────────────────────────

# class WorkerSettings:
#     functions = [embed_document]
#     redis_settings = RedisSettings(host="localhost", port=6379)

class WorkerSettings:
    functions = [embed_document]
    redis_settings = get_redis_settings()

# ── Enqueue helper (called from the API) ──────────────────────

# async def enqueue_embed(document_id: str):
#     pool = await create_pool(RedisSettings(host="localhost", port=6379))
#     await pool.enqueue_job("embed_document", document_id)
#     await pool.aclose()

async def enqueue_embed(document_id: str):
    pool = await create_pool(get_redis_settings())
    await pool.enqueue_job("embed_document", document_id)
    await pool.aclose()
