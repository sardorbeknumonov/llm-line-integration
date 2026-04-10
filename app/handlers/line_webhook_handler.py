"""Handle incoming LINE webhook events — forward user messages to Sendbird AI Agent."""

from __future__ import annotations

import logging

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.db.database import (
    get_user_by_line_id,
    create_user,
    upsert_conversation,
)

logger = logging.getLogger(__name__)

# Dedup using LINE's webhookEventId
_processed_events: set[str] = set()


async def handle_line_events(
    line: LineClient,
    sendbird: SendbirdClient,
    events: list[dict],
) -> None:
    """
    Process LINE webhook events.

    Flow for each text message:
      1. Dedup / skip redeliveries
      2. Ensure Sendbird user exists (create if needed, store in DB)
      3. Get or create a Sendbird AI Agent channel
      4. Store conversation in DB as 'pending'
      5. Forward the message to Sendbird
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
        user_id = event.get("source", {}).get("userId", "")

        if not user_id:
            continue

        try:
            if event_type == "message":
                msg = event.get("message", {})
                if msg.get("type") == "text":
                    await _forward_to_sendbird(line, sendbird, user_id, msg["text"])

            elif event_type == "follow":
                # New follower — create user in Sendbird proactively
                await _ensure_user(sendbird, user_id)

        except Exception:
            logger.exception(
                "[LINE] Error handling event type=%s user=%s", event_type, user_id[:8]
            )


async def _ensure_user(sendbird: SendbirdClient, line_user_id: str) -> str:
    """
    Ensure the LINE user has a corresponding Sendbird user.
    Returns the sb_user_id.
    """
    sb_user_id = f"line_{line_user_id}"

    # Check DB first
    db_user = get_user_by_line_id(line_user_id)
    if db_user:
        return db_user["sb_user_id"]

    # Create in Sendbird
    await sendbird.create_user(sb_user_id)

    # Store in DB
    create_user(line_user_id, sb_user_id)
    logger.info("[LINE->SB] Registered user line=%s sb=%s", line_user_id[:8], sb_user_id)

    return sb_user_id


async def _forward_to_sendbird(
    line: LineClient,
    sendbird: SendbirdClient,
    line_user_id: str,
    text: str,
) -> None:
    """Forward a LINE text message to Sendbird AI Agent."""
    # Step 1: Ensure user exists
    sb_user_id = await _ensure_user(sendbird, line_user_id)

    # Step 2: Get or create channel
    channel_url = await sendbird.get_or_create_channel(sb_user_id)
    if not channel_url:
        logger.error("[LINE->SB] No channel for user %s", sb_user_id)
        return

    # Step 3: Store conversation in DB
    upsert_conversation(
        channel_url=channel_url,
        line_user_id=line_user_id,
        sb_user_id=sb_user_id,
        status="pending",
    )

    # Step 4: Send message to Sendbird
    sent = await sendbird.send_message(channel_url, sb_user_id, text)
    if sent:
        logger.info(
            "[LINE->SB] Forwarded: user=%s channel=%s msg='%s'",
            line_user_id[:8], channel_url[:20], text[:80],
        )
    else:
        logger.error("[LINE->SB] Failed to forward message for %s", line_user_id[:8])
