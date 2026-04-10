"""Convert Sendbird AI Agent message to LINE message objects.

Parses the `data` field (JSON string) from AI Agent messages and
builds the appropriate LINE message format (Flex Carousel, Buttons,
Quick Reply, or plain text).
"""

from __future__ import annotations

import json
import logging

from app.models.messages import (
    FoodCarouselData,
    OrderConfirmationData,
    ButtonsData,
    QuickReplyData,
)
from app.builders.flex_carousel import (
    build_food_carousel,
    build_order_confirmation_bubble,
    build_buttons_bubble,
)

logger = logging.getLogger(__name__)


def convert_to_line_messages(content: str, data: str | None = None) -> list[dict]:
    """
    Convert an AI Agent message into LINE message objects.

    Args:
        content: Plain text content (always present).
        data: Optional JSON string with structured payload.

    Returns:
        List of LINE message dicts ready for push/reply API.
    """
    # Try to parse structured data
    if data:
        try:
            parsed = json.loads(data)
            msg_type = parsed.get("type", "")
            messages = _build_rich_messages(msg_type, parsed, content)
            if messages:
                return messages
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse message data: %s — falling back to text", e)

    # Default: plain text
    if content:
        return [{"type": "text", "text": content}]
    return []


def _build_rich_messages(
    msg_type: str, parsed: dict, content: str
) -> list[dict] | None:
    """Build rich LINE messages based on the structured data type."""
    handler = _TYPE_HANDLERS.get(msg_type)
    if handler:
        return handler(parsed, content)
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TYPE HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _handle_food_carousel(parsed: dict, content: str) -> list[dict]:
    """Convert food_carousel data to LINE Flex Carousel."""
    data = FoodCarouselData(**parsed)
    if not data.items:
        return [{"type": "text", "text": content or "No food items found."}]

    carousel = build_food_carousel(data.items)
    messages: list[dict] = []

    # Optional header text
    header = data.header_text or content
    if header:
        messages.append({"type": "text", "text": header})

    messages.append({
        "type": "flex",
        "altText": f"Found {len(data.items)} food item(s)",
        "contents": carousel,
    })
    return messages


def _handle_order_confirmation(parsed: dict, content: str) -> list[dict]:
    """Convert order_confirmation data to LINE Flex Bubble."""
    data = OrderConfirmationData(**parsed)
    bubble = build_order_confirmation_bubble(data)

    messages: list[dict] = []
    if content:
        messages.append({"type": "text", "text": content})
    messages.append({
        "type": "flex",
        "altText": f"Order {data.order_id} confirmed",
        "contents": bubble,
    })
    return messages


def _handle_buttons(parsed: dict, content: str) -> list[dict]:
    """Convert buttons data to LINE Flex Bubble with action buttons."""
    data = ButtonsData(**parsed)
    if not data.actions:
        return [{"type": "text", "text": content or data.text or "Please choose an option."}]

    bubble = build_buttons_bubble(data)
    messages: list[dict] = []
    if content and content != data.text:
        messages.append({"type": "text", "text": content})
    messages.append({
        "type": "flex",
        "altText": data.title or "Choose an option",
        "contents": bubble,
    })
    return messages


def _handle_quick_reply(parsed: dict, content: str) -> list[dict]:
    """Convert quick_reply data to LINE text message with quick reply items."""
    data = QuickReplyData(**parsed)
    if not data.options:
        return [{"type": "text", "text": content or data.text}]

    items = []
    for option in data.options[:13]:  # LINE max 13 quick reply items
        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": option[:20],  # LINE max label 20 chars
                "text": option,
            },
        })

    return [{
        "type": "text",
        "text": data.text or content or "Please choose:",
        "quickReply": {"items": items},
    }]


# ── Handler registry ────────────────────────────

_TYPE_HANDLERS = {
    "food_carousel": _handle_food_carousel,
    "order_confirmation": _handle_order_confirmation,
    "buttons": _handle_buttons,
    "quick_reply": _handle_quick_reply,
}
