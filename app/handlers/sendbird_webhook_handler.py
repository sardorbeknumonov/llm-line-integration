"""Handle incoming Sendbird webhooks — forward AI Agent responses to LINE."""

from __future__ import annotations

import logging

from app.services.line_client import LineClient
from app.builders.message_converter import convert_to_line_messages

logger = logging.getLogger(__name__)


async def handle_sendbird_event(
    line: LineClient,
    payload: dict,
) -> None:
    """
    Process Sendbird webhook events.

    Handles `message:ai_agent_sent` — AI Agent responses.
    Extracts message content and optional data field,
    converts to LINE message format, and pushes to LINE user.
    """
    category = payload.get("category", "")
    logger.info("[SB] Webhook received: category=%s", category)

    if category == "message:ai_agent_sent":
        await _handle_ai_agent_message(line, payload)
    else:
        logger.debug("[SB] Ignoring webhook category: %s", category)


async def _handle_ai_agent_message(line: LineClient, payload: dict) -> None:
    """
    Handle AI Agent response and push to LINE user.

    Webhook payload structure:
    {
        "category": "message:ai_agent_sent",
        "data": {
            "conversation": {"user_id": "line_U123..."},
            "message": {
                "message_id": 123,
                "content": "Here are some chicken options!",
                "data": "{\"type\":\"food_carousel\",\"items\":[...]}"
            }
        }
    }
    """
    data = payload.get("data", {})
    sb_user_id = data.get("conversation", {}).get("user_id", "")
    message = data.get("message", {})
    content = message.get("content", "")
    message_data = message.get("data")  # Optional JSON string

    if not sb_user_id or not content:
        logger.warning("[SB] Missing user_id or content in webhook payload")
        return

    # Derive LINE user ID from Sendbird user ID
    if not sb_user_id.startswith("line_"):
        logger.debug("[SB] Ignoring non-LINE user: %s", sb_user_id)
        return

    line_user_id = sb_user_id.removeprefix("line_")

    logger.info(
        "[SB->LINE] user=%s content='%s' has_data=%s",
        line_user_id[:8],
        content[:80],
        bool(message_data),
    )

    # Convert AI Agent message to LINE message objects
    line_messages = convert_to_line_messages(content, message_data)

    if not line_messages:
        logger.warning("[SB->LINE] No messages to send for user %s", line_user_id[:8])
        return

    # Push to LINE (can send up to 5 messages per API call)
    try:
        await line.push(line_user_id, line_messages)
    except Exception:
        logger.exception("[SB->LINE] Failed to push message to %s", line_user_id[:8])
