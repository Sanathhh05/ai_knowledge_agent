"""
RAG Service — orchestrates the full pipeline for chat turns.
"""
from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.chat import Conversation, ChatMessage, MessageRole
from app.services.vector_search_service import search_similar_chunks
from app.services.llm_service import generate_answer
from app.schemas.chat import CitationResponse, MessageResponse, ChatTurnResponse

def _get_conversation_history(db: Session, conversation_id: uuid.UUID, limit: int = 8) -> list[dict]:
    """Retrieve the recent chat history for a conversation."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = db.execute(stmt).scalars().all()
    # Reverse to get chronological order for the prompt
    history = []
    for msg in reversed(messages):
        history.append({
            "role": msg.role.value,
            "content": msg.content
        })
    return history

def process_chat_message(
    db: Session,
    conversation: Conversation,
    user_id: uuid.UUID,
    message_content: str,
    top_k: int = 5
) -> ChatTurnResponse:
    """
    Process a new user message:
    1. Save user message.
    2. Get recent history.
    3. Retrieve relevant chunks via vector search.
    4. Generate AI answer.
    5. Save AI message.
    6. Return response with citations.
    """
    # 1. Save user message
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message_content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # 2. Retrieve history (excluding the one we just saved)
    # The history query gets the latest `limit` messages.
    history = _get_conversation_history(db, conversation.id, limit=9)
    # Exclude the current message from the "history" passed to the LLM (it goes in CURRENT QUESTION)
    if history and history[-1]["content"] == message_content:
        history = history[:-1]

    # 3. Vector search
    retrieved_chunks = search_similar_chunks(db, query=message_content, user_id=user_id, top_k=top_k)
    
    # 4. Generate answer
    answer_text = generate_answer(
        query=message_content,
        context_chunks=retrieved_chunks,
        chat_history=history
    )
    
    # 5. Save AI message
    ai_msg = ChatMessage(
        conversation_id=conversation.id,
        user_id=user_id,
        role=MessageRole.ASSISTANT,
        content=answer_text
    )
    db.add(ai_msg)
    
    from datetime import datetime, timezone
    # Update conversation updated_at
    conversation.updated_at = datetime.now(timezone.utc) # trigger update
    db.commit()
    db.refresh(ai_msg)
    db.refresh(conversation)
    
    # 6. Format citations
    citations = []
    for chunk in retrieved_chunks:
        citations.append(
            CitationResponse(
                source_id=chunk["source_id"],
                source_name=chunk["source_name"],
                chunk_id=chunk["chunk_id"],
                score=chunk["score"],
                metadata=chunk["metadata"]
            )
        )
        
    return ChatTurnResponse(
        message=MessageResponse.model_validate(ai_msg),
        user_message=MessageResponse.model_validate(user_msg),
        sources=citations
    )
