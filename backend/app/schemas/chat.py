from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.models.chat import MessageRole

class CitationResponse(BaseModel):
    source_id: str
    source_name: str
    chunk_id: str
    score: float
    metadata: Dict[str, Any]

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatTurnResponse(BaseModel):
    message: MessageResponse
    user_message: Optional[MessageResponse] = None
    sources: List[CitationResponse] = []

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []
