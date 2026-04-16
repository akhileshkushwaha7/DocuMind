from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Message
from datetime import datetime, timedelta, timezone
# from datetime import datetime, timezone

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin)
):
    offset = (page - 1) * page_size
    query = select(User)
    if search:
        query = query.where(User.email.ilike(f"%{search}%"))

    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    # Get doc count per user
    doc_counts_result = await db.execute(
        select(Document.user_id, func.count(Document.id).label("count"))
        .group_by(Document.user_id)
    )
    doc_counts = {row.user_id: row.count for row in doc_counts_result}

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar()

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "doc_count": doc_counts.get(u.id, 0),
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

# @router.get("/stats")
# async def get_stats(
#     db: AsyncSession = Depends(get_db),
#     _=Depends(require_admin)
# ):
#     # Totals
#     total_users = (await db.execute(select(func.count(User.id)))).scalar()
#     total_docs = (await db.execute(select(func.count(Document.id)))).scalar()
#     total_messages = (await db.execute(select(func.count(Message.id)))).scalar()

#     # Uploads per day — last 30 days
#     # since = datetime.now(timezone.utc) - timedelta(days=29)
#     since = datetime.utcnow() - timedelta(days=29)

#     # uploads_result = await db.execute(
#     #     select(
#     #         cast(Document.created_at, Date).label("date"),
#     #         func.count(Document.id).label("count")
#     #     )
#     #     .where(Document.created_at >= since)
#     #     .group_by(cast(Document.created_at, Date))
#     #     .order_by(cast(Document.created_at, Date))
#     # )
#     uploads_result = await db.execute(
#     select(
#         func.date(Document.created_at).label("date"),
#         func.count(Document.id).label("count")
#     )
#     .where(Document.created_at >= since)
#     .group_by(func.date(Document.created_at))
#     .order_by(func.date(Document.created_at)))

#     uploads_by_day = [
#         {"date": str(row.date), "count": row.count}
#         for row in uploads_result
#     ]

#     # Fill in missing days with 0
#     all_days = {}
#     for i in range(30):
#         day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
#         all_days[day] = 0
#     for row in uploads_by_day:
#         all_days[row["date"]] = row["count"]

#     return {
#         "total_users": total_users,
#         "total_docs": total_docs,
#         "total_messages": total_messages,
#         "uploads_by_day": [{"date": k, "count": v} for k, v in all_days.items()],
#     }

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin)
):
    # Totals
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_docs = (await db.execute(select(func.count(Document.id)))).scalar()
    total_messages = (await db.execute(select(func.count(Message.id)))).scalar()

    # Last 30 days
    since = datetime.utcnow() - timedelta(days=29)

    uploads_result = await db.execute(
        select(
            func.date(Document.created_at).label("date"),
            func.count(Document.id).label("count")
        )
        .where(Document.created_at >= since)
        .group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
    )

    rows = uploads_result.all()

    # Normalize DB data
    uploads_by_day = [
        {"date": row.date.strftime("%Y-%m-%d"), "count": row.count}
        for row in rows
    ]

    # Fill missing days
    all_days = {}

    for i in range(30):
        day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        all_days[day] = 0

    for row in uploads_by_day:
        all_days[row["date"]] = row["count"]

    # Sort for frontend chart
    final_data = [
        {"date": k, "count": v}
        for k, v in sorted(all_days.items())
    ]

    return {
        "total_users": total_users,
        "total_docs": total_docs,
        "total_messages": total_messages,
        "uploads_by_day": final_data,
    }
