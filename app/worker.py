import asyncio
import structlog
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
import uuid
import os
import traceback

log = structlog.get_logger()
import sys

# Add after imports, around line 144
print(f"🚀 Worker starting with PID {os.getpid()}", file=sys.stderr, flush=True)
log.info("worker_started", pid=os.getpid())

# ── Redis config ──────────────────────────────────────────────

# def get_redis_settings() -> RedisSettings:
#     url = os.getenv("REDIS_URL", "redis://localhost:6379")
#     host = url.split("//")[1].split(":")[0]
#     port = int(url.split(":")[-1])
#     return RedisSettings(host=host, port=port)

from arq.connections import RedisSettings
import os

def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(os.environ["REDIS_URL"])


# ── 🔥 LOAD MODEL ONCE (CRITICAL FIX) ──────────────────────────
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


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
    qdrant = QdrantClient(url=cfg.QDRANT_URL)

    async with Session() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()

        if not doc:
            log.error("document_not_found", document_id=document_id)
            return

        doc.status = DocumentStatus.processing
        await db.commit()
        log.info("document_status_changed", document_id=document_id, status="processing")

        try:
            # 1. Extract PDF text
            log.info("extracting_pdf_text", document_id=document_id, file_path=doc.file_path)
            pdf = fitz.open(doc.file_path)
            full_text = "\n".join(page.get_text() for page in pdf)
            pdf.close()
            log.info("pdf_extracted", document_id=document_id, text_length=len(full_text))

            # 2. Chunking
            log.info("chunking_text", document_id=document_id)
            enc = tiktoken.get_encoding("cl100k_base")
            tokens = enc.encode(full_text)

            chunk_size, overlap = 500, 50
            chunks = []
            start = 0

            while start < len(tokens):
                chunk_tokens = tokens[start:start + chunk_size]
                chunks.append(enc.decode(chunk_tokens))
                start += chunk_size - overlap

            log.info("text_chunked", document_id=document_id, num_chunks=len(chunks))

            # 3. 🔥 EMBEDDING (FIXED - with proper await)
            log.info("embedding_chunks", document_id=document_id, num_chunks=len(chunks))
            try:
                vectors = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: model.encode(chunks, batch_size=4, show_progress_bar=False)
                    ),
                    timeout=300
                )
                vectors = vectors.tolist()
                log.info("embedding_complete", document_id=document_id, num_vectors=len(vectors))
            except asyncio.TimeoutError:
                log.error("embedding_timeout", document_id=document_id, timeout_seconds=300)
                doc.status = DocumentStatus.failed
                await db.commit()
                return

            # 4. Qdrant setup
            log.info("qdrant_setup_started", document_id=document_id, qdrant_url=cfg.QDRANT_URL)
            collection = "documents"
            existing = [c.name for c in qdrant.get_collections().collections]

            if collection not in existing:
                log.info("creating_qdrant_collection", collection=collection)
                qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                log.info("qdrant_collection_created", collection=collection)

            points = [
                PointStruct(
                    id=str(uuid.uuid5(uuid.UUID(document_id), str(i))),
                    vector=vectors[i],
                    payload={
                        "document_id": document_id,
                        "chunk_index": i,
                        "text": chunks[i]
                    }
                )
                for i in range(len(chunks))
            ]

            log.info("upserting_to_qdrant", document_id=document_id, num_points=len(points))
            qdrant.upsert(collection_name=collection, points=points)
            log.info("qdrant_upsert_complete", document_id=document_id)

            # 5. Mark ready
            doc.status = DocumentStatus.ready
            await db.commit()

            log.info("embed_job_done", document_id=document_id, chunks=len(chunks))

        except Exception as e:
            log.error(
                "embed_job_failed",
                document_id=document_id,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            doc.status = DocumentStatus.failed
            await db.commit()

    await engine.dispose()


# ── Worker config ──────────────────────────────────────────────

class WorkerSettings:
    functions = [embed_document]
    redis_settings = get_redis_settings()


# ── Enqueue helper ─────────────────────────────────────────────

async def enqueue_embed(document_id: str):
    """Enqueue a document for embedding"""
    try:
        pool = await create_pool(get_redis_settings())
        job = await pool.enqueue_job("embed_document", document_id)
        log.info("job_enqueued", document_id=document_id, job_id=str(job.job_id))
        await pool.aclose()
    except Exception as e:
        log.error(
            "enqueue_failed",
            document_id=document_id,
            error=str(e),
            traceback=traceback.format_exc()
        )
        raise
