# uvicorn app.main:app --reload 
# docker exec -it documind-postgres-1 psql -U documind -d documind -c "\dt"
# alembic -c backend/alembic.ini revision --autogenerate -m "create users table"
# alembic -c backend/alembic.ini upgrade head
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ZmI5NDgzZC1iYTYwLTQ3ZGItYWNhYi0zZGVkNjdiZTBkODgiLCJleHAiOjE3NzU3NzI3ODAsInR5cGUiOiJhY2Nlc3MifQ.Xi9BOJ3RxsM4UU_Cx5VWZAIPAqY9jRX0D7OLykGCeb0",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ZmI5NDgzZC1iYTYwLTQ3ZGItYWNhYi0zZGVkNjdiZTBkODgiLCJleHAiOjE3NzYzNzY2ODAsInR5cGUiOiJyZWZyZXNoIn0.NhhnXRHJd3gJMxbjGa8ruFmyBsEiEGzxZ9r0dNC9_hk",
#   "token_type": "bearer"
# }
#   "email": "chatal@gmail.com",
#   "password": "chatal"
# }'

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.routers import auth
# from app.routers import documents
# from app.routers import chat

# app = FastAPI(title="DocuMind API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(auth.router)
# app.include_router(documents.router)
# app.include_router(chat.router)
# app.include_router(admin.router)

# @app.get("/health")
# async def health():
#     return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, documents, chat, admin

app = FastAPI(title="DocuMind API")

from app.core.database import Base, engine

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://docu-mind-nu-one.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
