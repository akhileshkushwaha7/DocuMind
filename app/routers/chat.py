import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, MessageResponse
from app.services.rag import stream_chat
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/chat", tags=["chat"])

async def get_or_create_conversation(db: AsyncSession, user_id: str, doc_id: str) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.document_id == doc_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(user_id=user_id, document_id=doc_id)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    return conv

@router.post("/{doc_id}")
async def chat(
    doc_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Rate limit — 20 requests per minute per user
    await check_rate_limit(user.id)

    # Verify document is ready
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.ready:
        raise HTTPException(status_code=400, detail=f"Document is not ready yet. Status: {doc.status}")

    # Get or create conversation
    conv = await get_or_create_conversation(db, user.id, doc_id)

    # Load message history
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all()]

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=body.message)
    db.add(user_msg)
    await db.commit()

    # Stream response from RAG pipeline
    async def event_stream():
        full_response = ""
        try:
            async for token in stream_chat(doc_id, history, body.message):
                full_response += token
                # SSE format: data: <payload>\n\n
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Save complete assistant message after streaming finishes
            async with db.begin():
                assistant_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_response
                )
                db.add(assistant_msg)

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

@router.get("/{doc_id}/history", response_model=list[MessageResponse])
async def get_history(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user.id,
            Conversation.document_id == doc_id
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        return []

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()