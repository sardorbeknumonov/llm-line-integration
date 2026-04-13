"""Handle incoming Sendbird webhooks — conversation lifecycle + AI Agent responses."""

from __future__ import annotations

import json
import logging

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.builders.message_converter import convert_to_line_messages
from app.builders.sendbird_message_converter import convert_bot_message
from app.db.database import (
    update_conversation_status,
    upsert_conversation,
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

    elif category == "message:user_sent":
        await _handle_user_sent_on_closed(sendbird, payload)

    elif category == "conversation:started":
        _handle_conversation_started(payload)

    elif category == "conversation:closed":
        _handle_conversation_closed(payload)

    else:
        logger.debug("[SB] Ignoring webhook category: %s", category)


# ── Re-send on closed conversation ─────────────────


async def _handle_user_sent_on_closed(
    sendbird: SendbirdClient, payload: dict
) -> None:
    """
    Handle message:user_sent on a closed conversation.

    When a user sends a message to a closed channel, the AI Agent won't
    respond. Detect this, create a new channel, and re-send the message.
    """
    data = payload.get("data", {})
    conversation = data.get("conversation", {})
    status = conversation.get("status", "")
    sb_user_id = conversation.get("user_id", "")
    old_channel_url = conversation.get("channel_url", "")
    message_content = data.get("message", {}).get("content", "")

    if status != "closed":
        logger.debug("[SB] message:user_sent on active conversation, ignoring")
        return

    if not sb_user_id or not message_content:
        logger.warning("[SB] message:user_sent missing user_id or content")
        return

    logger.info(
        "[SB] User %s sent message on closed channel %s — re-routing to new channel",
        sb_user_id, old_channel_url[:30],
    )

    # Invalidate cached channel so a new one is created
    sendbird.invalidate_channel_cache(sb_user_id)

    # Update local DB
    update_conversation_status(old_channel_url, "closed")

    # Create new channel
    new_channel_url = await sendbird.get_or_create_channel(sb_user_id)
    if not new_channel_url:
        logger.error("[SB] Failed to create new channel for %s", sb_user_id)
        return

    # Derive line_user_id for DB record
    line_user_id = sb_user_id.removeprefix("line_") if sb_user_id.startswith("line_") else ""
    if line_user_id:
        upsert_conversation(
            channel_url=new_channel_url,
            line_user_id=line_user_id,
            sb_user_id=sb_user_id,
            status="pending",
        )

    # Re-send the message to the new channel
    sent = await sendbird.send_message(new_channel_url, sb_user_id, message_content)
    if sent:
        logger.info(
            "[SB] Re-sent message to new channel: user=%s channel=%s msg='%s'",
            sb_user_id, new_channel_url[:30], message_content[:80],
        )
    else:
        logger.error("[SB] Failed to re-send message for %s", sb_user_id)


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
      1. extended_message_payload with function_calls → rich LINE messages
         (Flex Carousels, Flex Bubbles, Quick Replies)
      2. message_data (structured JSON) → legacy converter
      3. extended_message_payload with suggested_replies only → text + quick replies
      4. Plain content → text message
    """
    # Priority 1: Use new converter for extended_payload with function_calls
    if extended_payload and extended_payload.get("function_calls"):
        messages = convert_bot_message(content, extended_payload)
        if messages:
            return messages

    # Priority 2: Try legacy structured data
    if message_data:
        messages = convert_to_line_messages(content, message_data)
        if messages:
            return messages

    # Priority 3 & 4: Text with optional suggested_replies
    if not content:
        return []

    # Use new converter for suggested_replies without function_calls
    if extended_payload:
        messages = convert_bot_message(content, extended_payload)
        if messages:
            return messages

    return [{"type": "text", "text": content}]
