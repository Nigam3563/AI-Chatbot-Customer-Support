
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import Conversation, Message
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.ai_service import generate_ai_response


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post(
    "/conversations",
    response_model=ConversationResponse,
)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
):
    conversation = Conversation(title=data.title)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: Session = Depends(get_db),
):
    return (
        db.query(Conversation)
        .order_by(Conversation.id.desc())
        .all()
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    # Check whether the conversation exists.
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # Validate the incoming message.
    content = data.content.strip()

    if not content:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty",
        )

    # Save the customer's message.
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Generate the AI response.
    try:
        answer = generate_ai_response(content)

        if not answer or not answer.strip():
            raise RuntimeError("Gemini returned an empty response")

        answer = answer.strip()

    except Exception as exc:
        logger.exception(
            "Gemini response generation failed for conversation_id=%s",
            conversation_id,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not generate an AI response. "
                "Check the backend logs for the actual error."
            ),
        ) from exc

    # Save the assistant's response.
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    try:
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to save AI response for conversation_id=%s",
            conversation_id,
        )
        raise HTTPException(
            status_code=500,
            detail="The AI responded, but the response could not be saved.",
        )

    # Return both messages in the format expected by the frontend.
    return [user_message, assistant_message]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .all()
    )
