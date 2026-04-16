import structlog
from groq import AsyncGroq
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.core.config import settings

log = structlog.get_logger()
groq = AsyncGroq(api_key=settings.GROQ_API_KEY)
qdrant = QdrantClient(url=settings.QDRANT_URL)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
COLLECTION = "documents"

def embed_query(text: str) -> list[float]:
    return embedder.encode(text).tolist()

async def search_chunks(document_id: str, query_vector: list[float], top_k: int = 5) -> list[str]:
    results = qdrant.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        query_filter={
            "must": [{"key": "document_id", "match": {"value": document_id}}]
        },
        limit=top_k
    )
    return [hit.payload["text"] for hit in results]

def build_prompt(chunks: list[str], history: list[dict], user_message: str) -> list[dict]:
    context = "\n\n---\n\n".join(chunks)
    system = f"""You are a helpful assistant that answers questions about a document.
Use ONLY the context below to answer. If the answer is not in the context, say so clearly.

DOCUMENT CONTEXT:
{context}"""
    messages = [{"role": "system", "content": system}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages

async def stream_chat(document_id: str, history: list[dict], user_message: str):
    log.info("rag_start", document_id=document_id)

    query_vector = embed_query(user_message)
    chunks = await search_chunks(document_id, query_vector)

    if not chunks:
        yield "I couldn't find relevant information in this document."
        return

    messages = build_prompt(chunks, history, user_message)

    # Stream answer from Groq (free, fast)
    stream = await groq.chat.completions.create(
        model="llama-3.1-8b-instant",   # free model on Groq
        messages=messages,
        stream=True,
        temperature=0.3,
        max_tokens=1000
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

    log.info("rag_done", document_id=document_id)