"""Handle incoming Sendbird webhooks — conversation lifecycle + AI Agent responses."""

from __future__ import annotations

import json
import logging

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.builders.message_converter import convert_to_line_messages
from app.db.database import (
    update_conversation_status,
    get_user_by_sb_id,
)

logger = logging.getLogger(__name__)


async def handle_sendbird_event(
    line: LineClient,
    sendbird: SendbirdClient,
    payload: dict,
) -> None:
    """
    Route Sendbird webhook events.

    Handled categories:
      - message:ai_agent_sent    → forward AI response to LINE
      - ai_agent:conversation_started  → mark conversation as 'ongoing'
      - ai_agent:conversation_closed   → mark conversation as 'closed'
    """
    category = payload.get("category", "")
    logger.info("[SB] Webhook received: category=%s", category)

    if category == "message:ai_agent_sent":
        await _handle_ai_agent_message(line, sendbird, payload)

    elif category == "conversation:started":
        _handle_conversation_started(payload)

    elif category == "conversation:closed":
        _handle_conversation_closed(payload)

    else:
        logger.debug("[SB] Ignoring webhook category: %s", category)


# ── Conversation lifecycle ─────────────────────────


def _handle_conversation_started(payload: dict) -> None:
    """Mark conversation as ongoing in the DB."""
    data = payload.get("data", {})
    channel_url = data.get("conversation", {}).get("channel_url", "")

    if not channel_url:
        logger.warning("[SB] CONVERSATION_STARTED missing channel_url")
        return

    update_conversation_status(channel_url, "ongoing")
    logger.info("[SB] Conversation started: %s", channel_url[:30])


def _handle_conversation_closed(payload: dict) -> None:
    """Mark conversation as closed in the DB."""
    data = payload.get("data", {})
    channel_url = data.get("conversation", {}).get("channel_url", "")

    if not channel_url:
        logger.warning("[SB] CONVERSATION_CLOSED missing channel_url")
        return

    update_conversation_status(channel_url, "closed")
    logger.info("[SB] Conversation closed: %s", channel_url[:30])


# ── AI Agent message → LINE ───────────────────────


async def _handle_ai_agent_message(
    line: LineClient, sendbird: SendbirdClient, payload: dict
) -> None:
    """
    Forward AI Agent response to the LINE user.

    Flow:
      1. Extract user ID and message from webhook
      2. Look up LINE user ID from DB (sb_user_id -> line_user_id)
      3. Optionally fetch extended_message_payload for rich content
      4. Build LINE messages and push
    """
    data = payload.get("data", {})
    conversation = data.get("conversation", {})
    sb_user_id = conversation.get("user_id", "")
    channel_url = conversation.get("channel_url", "")
    message = data.get("message", {})
    message_id = message.get("message_id")
    content = message.get("content", "")

    if not sb_user_id or not content:
        logger.warning("[SB] Missing user_id or content in webhook payload")
        return

    # Look up LINE user ID from DB
    db_user = get_user_by_sb_id(sb_user_id)
    if not db_user:
        # Fallback: derive from sb_user_id convention
        if not sb_user_id.startswith("line_"):
            logger.debug("[SB] Ignoring non-LINE user: %s", sb_user_id)
            return
        line_user_id = sb_user_id.removeprefix("line_")
    else:
        line_user_id = db_user["line_user_id"]

    # Fetch full message with extended_message_payload from Platform API
    extended_payload = None
    if message_id and channel_url:
        full_message = await sendbird.get_message(channel_url, message_id)
        if full_message:
            extended_payload = full_message.get("extended_message_payload")
            logger.info(
                "[SB] Extended payload: %s",
                json.dumps(extended_payload, ensure_ascii=False) if extended_payload else "None",
            )

    # Parse message.data field if present
    message_data = message.get("data")
    if isinstance(message_data, dict):
        message_data = json.dumps(message_data)

    logger.info(
        "[SB->LINE] user=%s content='%s' has_extended=%s",
        line_user_id[:8],
        content[:80],
        bool(extended_payload),
    )

    # Build LINE messages
    line_messages = _build_line_messages(content, message_data, extended_payload)

    if not line_messages:
        logger.warning("[SB->LINE] No messages to send for user %s", line_user_id[:8])
        return

    # Push to LINE
    try:
        await line.push(line_user_id, line_messages)
    except Exception:
        logger.exception("[SB->LINE] Failed to push message to %s", line_user_id[:8])


def _build_line_messages(
    content: str,
    message_data: str | None,
    extended_payload: dict | None,
) -> list[dict]:
    """
    Build LINE messages from AI Agent response.

    Priority:
      1. message_data (structured JSON) → rich LINE messages via converter
      2. extended_message_payload.suggested_replies → text + quick replies
      3. Plain content → text message
    """
    # Try structured data first
    if message_data:
        messages = convert_to_line_messages(content, message_data)
        if messages:
            if extended_payload:
                _attach_quick_replies(messages, extended_payload)
            return messages

    # Build text message
    if not content:
        return []

    msg: dict = {"type": "text", "text": content}

    # Attach suggested_replies from extended payload as quick replies
    if extended_payload:
        suggested = extended_payload.get("suggested_replies", [])
        if suggested:
            msg["quickReply"] = {
                "items": [
                    {
                        "type": "action",
                        "action": {
                            "type": "message",
                            "label": reply[:20],
                            "text": reply,
                        },
                    }
                    for reply in suggested[:13]  # LINE max 13
                ]
            }

    return [msg]


def _attach_quick_replies(messages: list[dict], extended_payload: dict) -> None:
    """Attach suggested_replies from extended_message_payload to the last LINE message."""
    suggested = extended_payload.get("suggested_replies", [])
    if not suggested or not messages:
        return

    last_msg = messages[-1]
    if "quickReply" in last_msg:
        return

    last_msg["quickReply"] = {
        "items": [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": reply[:20],
                    "text": reply,
                },
            }
            for reply in suggested[:13]
        ]
    }
