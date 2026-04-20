import os, shutil, uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.cache import get_cached, set_cached, invalidate
UPLOAD_DIR = "uploads"
router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        user_id=user.id,
        filename=file.filename,
        file_path=file_path,
    )
    db.add(doc)
    
    await db.commit()
    await db.refresh(doc)

    # Enqueue embedding job (we'll wire this in Step 22)
    from app.worker import enqueue_embed
    await enqueue_embed(doc.id)

    return doc

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .offset(offset).limit(page_size)
    )
    docs = result.scalars().all()
    count = await db.execute(select(func.count()).where(Document.user_id == user.id))
    return DocumentListResponse(items=docs, total=count.scalar(), page=page, page_size=page_size)

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    cache_key = f"doc:{doc_id}:{user.id}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    data = DocumentResponse.model_validate(doc).model_dump(mode="json")
    await set_cached(cache_key, data, ttl=60)
    return doc

@router.get("/{doc_id}/status")
async def get_status(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.status}

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await invalidate(f"doc:{doc_id}:{user.id}")
    await db.delete(doc)
    await db.commit()
    return {"detail": "Deleted"}

# import os, shutil, uuid, asyncio
# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func
# from app.core.database import get_db
# from app.core.deps import get_current_user
# from app.models.user import User
# from app.models.document import Document, DocumentStatus
# from app.schemas.document import DocumentResponse, DocumentListResponse
# from app.services.cache import get_cached, set_cached, invalidate
# from app.worker import embed_document  # ✅ import worker function

# UPLOAD_DIR = "uploads"
# router = APIRouter(prefix="/documents", tags=["documents"])


# @router.post("/upload", response_model=DocumentResponse)
# async def upload_document(
#     file: UploadFile = File(...),
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are supported")

#     file_id = str(uuid.uuid4())
#     file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
#     os.makedirs(UPLOAD_DIR, exist_ok=True)

#     with open(file_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     doc = Document(
#         user_id=user.id,
#         filename=file.filename,
#         file_path=file_path,
#         status=DocumentStatus.processing  # start as processing
#     )
#     db.add(doc)
    
#     await db.commit()
#     await db.refresh(doc)

#     # ✅ Run embedding in background (FREE solution)
#     asyncio.create_task(embed_document(None, str(doc.id)))

#     return doc


# @router.get("/", response_model=DocumentListResponse)
# async def list_documents(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(10, ge=1, le=50),
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     offset = (page - 1) * page_size
#     result = await db.execute(
#         select(Document)
#         .where(Document.user_id == user.id)
#         .order_by(Document.created_at.desc())
#         .offset(offset).limit(page_size)
#     )
#     docs = result.scalars().all()
#     count = await db.execute(select(func.count()).where(Document.user_id == user.id))
#     return DocumentListResponse(items=docs, total=count.scalar(), page=page, page_size=page_size)


# @router.get("/{doc_id}", response_model=DocumentResponse)
# async def get_document(
#     doc_id: str,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     cache_key = f"doc:{doc_id}:{user.id}"
#     cached = await get_cached(cache_key)
#     if cached:
#         return cached

#     result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
#     doc = result.scalar_one_or_none()
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")

#     data = DocumentResponse.model_validate(doc).model_dump(mode="json")
#     await set_cached(cache_key, data, ttl=60)
#     return doc


# @router.get("/{doc_id}/status")
# async def get_status(
#     doc_id: str,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
#     doc = result.scalar_one_or_none()
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return {"status": doc.status}


# @router.delete("/{doc_id}")
# async def delete_document(
#     doc_id: str,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user.id))
#     doc = result.scalar_one_or_none()
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")

#     if os.path.exists(doc.file_path):
#         os.remove(doc.file_path)

#     await invalidate(f"doc:{doc_id}:{user.id}")
#     await db.delete(doc)
#     await db.commit()

#     return {"detail": "Deleted"}



