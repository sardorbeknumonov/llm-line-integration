"""Handle incoming LINE webhook events — route to conversation state machine."""

from __future__ import annotations

import logging

from app.services.line_client import LineClient
from app.handlers.conversation_handler import handle_conversation

logger = logging.getLogger(__name__)

# Dedup using LINE's webhookEventId
_processed_events: set[str] = set()


async def handle_line_events(
    line: LineClient,
    events: list[dict],
) -> None:
    """
    Process LINE webhook events and route to the conversation handler.

    Handles:
      - text messages → conversation state machine
      - follow events → send greeting
    """
    for event in events:
        event_id = event.get("webhookEventId", "")

        # Dedup
        if event_id and event_id in _processed_events:
            logger.debug("[LINE] Duplicate event %s, skipping", event_id)
            continue
        if event_id:
            _processed_events.add(event_id)

        # Skip redeliveries
        if event.get("deliveryContext", {}).get("isRedelivery", False):
            logger.debug("[LINE] Redelivery event, skipping")
            continue

        event_type = event.get("type", "")
        reply_token = event.get("replyToken", "")
        user_id = event.get("source", {}).get("userId", "")

        if not user_id:
            continue

        try:
            if event_type == "message":
                msg = event.get("message", {})
                if msg.get("type") == "text":
                    await handle_conversation(line, user_id, reply_token, msg["text"])
                else:
                    await line.reply_text(
                        reply_token,
                        "\U0001f37d\ufe0f I can help you order food! "
                        "Just type 'Hello' to get started.",
                    )

            elif event_type == "follow":
                # New follower → send greeting
                await handle_conversation(line, user_id, reply_token, "hello")

            elif event_type == "postback":
                # Forward postback displayText as text
                postback = event.get("postback", {})
                text = postback.get("displayText") or postback.get("data", "")
                if text:
                    await handle_conversation(line, user_id, reply_token, text)

        except Exception:
            logger.exception(
                "[LINE] Error handling event type=%s user=%s", event_type, user_id[:8]
            )
