"""
LLM service using MRM-GENI model.
Builds full conversation history from the database on every call so
context is always accurate, even after server restarts.
"""

import logging
import requests
from core.exceptions import LLMAPIError

logger = logging.getLogger('llm')

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "MRM-GENI"


def generate_llm_response(
    conversation_id: int,
    user_message: str,
    conversation_obj=None,
) -> str:
    """
    Generate a response from the Ollama LLM, sending the full conversation
    history so the model maintains context across turns.

    The user message has already been saved to the DB by the caller before
    this function is invoked, so loading all DB messages gives us the
    complete history including the current turn.
    """
    from apps.conversations.models import Message

    # Build history from every message in the conversation (including the
    # just-saved user message), ordered chronologically.
    messages = list(
        Message.objects.filter(conversation_id=conversation_id)
        .order_by('timestamp')
        .values('role', 'content')
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }

    logger.debug(
        f"Calling MRM GENI for conversation {conversation_id} "
        f"with {len(messages)} messages in history"
    )

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to MRM GENI at %s", OLLAMA_URL)
        raise LLMAPIError("LLM service is not reachable. Make sure Ollama is running.")
    except requests.exceptions.Timeout:
        logger.error("MRM GENI request timed out for conversation %s", conversation_id)
        raise LLMAPIError("LLM service timed out. Please try again.")
    except requests.exceptions.HTTPError as e:
        logger.error("MRM GENI returned HTTP %s: %s", response.status_code, response.text)
        raise LLMAPIError(f"LLM service error: {e}")

    try:
        reply = response.json()["message"]["content"]
    except (KeyError, ValueError) as e:
        logger.error("Unexpected MRM GENI response format: %s", response.text)
        raise LLMAPIError("Unexpected response format from LLM service.")

    logger.info(
        "Generated response for conversation %s (%d chars)",
        conversation_id, len(reply)
    )
    return reply.strip()


def clear_conversation_memory(conversation_id: int):
    """No-op — history is loaded from DB on every call, nothing to clear."""
    pass
