from pydantic import BaseModel
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int