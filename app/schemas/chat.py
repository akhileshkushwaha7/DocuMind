from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    document_id: str
    messages: list[MessageResponse]

    class Config:
        from_attributes = True