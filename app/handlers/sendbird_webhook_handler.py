"""Handle incoming Sendbird webhooks — forward AI Agent responses to LINE."""

from __future__ import annotations

import json
import logging

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.builders.message_converter import convert_to_line_messages

logger = logging.getLogger(__name__)


async def handle_sendbird_event(
    line: LineClient,
    sendbird: SendbirdClient,
    payload: dict,
) -> None:
    """
    Process Sendbird webhook events.

    Handles `message:ai_agent_sent` — AI Agent responses.
    1. Extract message_id and channel_url from webhook
    2. Fetch full message via Platform API (includes extended_message_payload)
    3. Build LINE messages from content + extended payload (suggested_replies, etc.)
    4. Push to LINE user
    """
    category = payload.get("category", "")
    logger.info("[SB] Webhook received: category=%s", category)

    if category == "message:ai_agent_sent":
        await _handle_ai_agent_message(line, sendbird, payload)
    else:
        logger.debug("[SB] Ignoring webhook category: %s", category)


async def _handle_ai_agent_message(
    line: LineClient, sendbird: SendbirdClient, payload: dict
) -> None:
    """
    Handle AI Agent response and push to LINE user.

    Webhook payload structure (message:ai_agent_sent):
    {
        "category": "message:ai_agent_sent",
        "data": {
            "ai_agent_id": "81199735-...",
            "conversation": {
                "user_id": "line_U123...",
                "channel_url": "sendbird_group_channel_...",
                "status": "open"
            },
            "message": {
                "message_id": 10062204441,
                "content": "Hello Margaret! ..."
            }
        }
    }
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

    # Derive LINE user ID from Sendbird user ID
    if not sb_user_id.startswith("line_"):
        logger.debug("[SB] Ignoring non-LINE user: %s", sb_user_id)
        return

    line_user_id = sb_user_id.removeprefix("line_")

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

    # Parse message.data field if present (from webhook)
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
            # Attach suggested_replies as quick replies to the last message
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
    # Don't overwrite existing quick replies
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
