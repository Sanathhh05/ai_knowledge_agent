from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
from typing import List
import tempfile
import os

from app.database import get_db
from app.models.user import User
from app.models.chat import Conversation, ChatMessage
from app.routers.auth import get_current_user
from app.services.stt_service import transcribe_audio
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    MessageCreate,
    ChatTurnResponse,
    MessageResponse
)
from app.services.rag_service import process_chat_message

router = APIRouter(tags=["Conversations"])

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat conversation."""
    title = conv_in.title or "New Conversation"
    conv = Conversation(user_id=current_user.id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for the current user."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return db.execute(stmt).scalars().all()

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation and its messages."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    return conv

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and all its messages."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    db.delete(conv)
    db.commit()

@router.post("/{conversation_id}/messages", response_model=ChatTurnResponse)
def send_message(
    conversation_id: uuid.UUID,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a conversation and get an AI response."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    if not msg_in.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty")

    # Only set a dynamic title on the very first message if it's named "New Conversation"
    # To keep it simple, we check if title is default and there are no previous messages.
    if conv.title == "New Conversation":
        # Truncate first message to 40 chars
        new_title = msg_in.content.strip()[:40]
        if len(msg_in.content) > 40:
            new_title += "..."
        conv.title = new_title
        db.add(conv)
        db.commit()

    try:
        response = process_chat_message(
            db=db,
            conversation=conv,
            user_id=current_user.id,
            message_content=msg_in.content,
            top_k=5
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate response: {str(e)}")

@router.post("/{conversation_id}/voice", response_model=ChatTurnResponse)
async def send_voice_message(
    conversation_id: uuid.UUID,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transcribe voice, send to RAG, return text response."""
    conv = db.get(Conversation, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    
    # Save audio temporarily
    temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
    try:
        with os.fdopen(temp_fd, 'wb') as f:
            f.write(await audio.read())
            
        transcript = transcribe_audio(temp_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
            
    if not transcript or not transcript.strip():
        raise HTTPException(status_code=400, detail="I couldn't detect any speech. Please try again.")
        
    # Same logic for title as text chat
    if conv.title == "New Conversation":
        new_title = transcript.strip()[:40]
        if len(transcript) > 40:
            new_title += "..."
        conv.title = new_title
        db.add(conv)
        db.commit()

    try:
        response = process_chat_message(
            db=db,
            conversation=conv,
            user_id=current_user.id,
            message_content=transcript,
            top_k=5
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate response: {str(e)}")

