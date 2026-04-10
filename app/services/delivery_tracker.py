"""Simulated delivery tracking — background task that sends proactive push messages."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.services.line_client import LineClient
from app.builders.conversation_messages import (
    build_tracking_preparing,
    build_tracking_rider,
    build_tracking_delivered,
    build_review_rating_prompt,
)

if TYPE_CHECKING:
    from app.handlers.conversation_handler import UserSession, State

logger = logging.getLogger(__name__)


async def simulate_delivery(
    line: LineClient,
    line_user_id: str,
    session: "UserSession",
) -> None:
    """
    Run as an asyncio background task after payment.

    Sends 4 proactive push messages with delays:
      1. (5s)  Restaurant accepted, preparing food
      2. (10s) Rider is on the way
      3. (8s)  Order delivered!
      4. (2s)  Rating prompt
    """
    from app.handlers.conversation_handler import State

    restaurant_name = session.restaurant.name if session.restaurant else "The restaurant"

    try:
        # Step 1: Preparing
        await asyncio.sleep(5)
        messages = build_tracking_preparing(restaurant_name)
        await line.push(line_user_id, messages)
        logger.info("[TRACK] Preparing push sent to %s", line_user_id[:8])

        # Step 2: Rider on the way
        await asyncio.sleep(10)
        messages = build_tracking_rider()
        await line.push(line_user_id, messages)
        logger.info("[TRACK] Rider push sent to %s", line_user_id[:8])

        # Step 3: Delivered
        await asyncio.sleep(8)
        messages = build_tracking_delivered()
        await line.push(line_user_id, messages)
        logger.info("[TRACK] Delivered push sent to %s", line_user_id[:8])

        # Step 4: Rating prompt
        await asyncio.sleep(2)
        messages = build_review_rating_prompt()
        await line.push(line_user_id, messages)
        session.state = State.REVIEW_RATING
        logger.info("[TRACK] Rating prompt sent to %s", line_user_id[:8])

    except asyncio.CancelledError:
        logger.info("[TRACK] Delivery simulation cancelled for %s", line_user_id[:8])
    except Exception:
        logger.exception("[TRACK] Delivery simulation error for %s", line_user_id[:8])
