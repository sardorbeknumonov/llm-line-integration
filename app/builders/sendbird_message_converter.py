"""Convert Sendbird AI Agent bot messages to LINE message objects.

Parses `extended_message_payload` (function_calls, suggested_replies)
and builds appropriate LINE messages: Flex Carousels, Flex Bubbles,
Quick Replies, or plain text.

Usage:
    messages = convert_bot_message(message_text, extended_message_payload)
    await line_client.push(user_id, messages)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def convert_bot_message(
    text: str,
    payload: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Convert a Sendbird AI Agent bot message into LINE message objects.

    Args:
        text: The bot's text message content.
        payload: The extended_message_payload from the bot message.

    Returns:
        List of LINE message dicts ready for push/reply API.
    """
    if not payload:
        return [_text_msg(text)] if text else []

    function_calls = payload.get("function_calls", [])
    suggested_replies = payload.get("suggested_replies", [])

    messages: list[dict] = []

    if function_calls:
        tool_name = function_calls[0].get("name", "")
        response_text = function_calls[0].get("response", {}).get("response_text", "")
        tool_data = _safe_parse(response_text)

        handler = _TOOL_HANDLERS.get(tool_name)
        if handler and tool_data:
            messages = handler(text, tool_data)
        else:
            messages = [_text_msg(text)] if text else []
    else:
        messages = [_text_msg(text)] if text else []

    # Attach suggested_replies as Quick Reply to the LAST message
    if suggested_replies and messages:
        _attach_quick_reply(messages[-1], suggested_replies)

    return messages


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOOL HANDLERS — each returns list[dict] of LINE messages
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _handle_get_food_categories(text: str, data: dict) -> list[dict]:
    """Categories → text only (suggested_replies will show as Quick Reply)."""
    return [_text_msg(text)] if text else []


def _handle_search_restaurants(text: str, data: dict) -> list[dict]:
    """Restaurants → Flex Carousel cards."""
    restaurants = data.get("restaurants", [])
    if not restaurants:
        return [_text_msg(text)] if text else []

    bubbles = []
    for r in restaurants[:12]:
        bubble: dict = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": r.get("title") or r.get("name", ""), "weight": "bold", "size": "lg", "wrap": True, "maxLines": 2},
                    {"type": "text", "text": r.get("description", ""), "size": "sm", "color": "#888888", "wrap": True},
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": r.get("cta_label", "View Menu")[:20],
                            "text": r.get("title") or r.get("name", ""),
                        },
                        "style": "primary",
                        "color": "#E74C3C",
                        "height": "sm",
                    },
                ],
            },
        }
        image_url = r.get("image_url", "")
        if image_url:
            bubble["hero"] = {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            }
        bubbles.append(bubble)

    messages = []
    if text:
        messages.append(_text_msg(text))
    messages.append({
        "type": "flex",
        "altText": f"Found {len(bubbles)} restaurant(s)",
        "contents": {"type": "carousel", "contents": bubbles},
    })
    return messages


def _handle_get_restaurant_menu(text: str, data: dict) -> list[dict]:
    """Menu items → Flex Carousel cards with price."""
    items = data.get("items", [])
    restaurant_name = data.get("restaurant_name", "")
    if not items:
        return [_text_msg(text)] if text else []

    bubbles = []
    for item in items[:12]:
        body_contents = [
            {"type": "text", "text": item.get("name", ""), "weight": "bold", "size": "lg", "wrap": True, "maxLines": 2},
        ]
        desc = item.get("description", "")
        if desc:
            body_contents.append({"type": "text", "text": desc, "size": "sm", "color": "#888888", "wrap": True})

        price = item.get("price", 0)
        if price:
            body_contents.append({"type": "separator", "margin": "lg"})
            body_contents.append({
                "type": "box",
                "layout": "horizontal",
                "margin": "lg",
                "contents": [
                    {"type": "text", "text": "Price", "size": "sm", "color": "#999999"},
                    {"type": "text", "text": f"${price:.2f}", "size": "xl", "weight": "bold", "color": "#E74C3C", "align": "end"},
                ],
            })

        item_name = item.get("name", "")
        bubble: dict = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": body_contents,
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "\U0001f6d2 Order", "text": item_name},
                        "style": "primary",
                        "color": "#E74C3C",
                        "height": "sm",
                    },
                ],
            },
        }
        image_url = item.get("image_url", "")
        if image_url:
            bubble["hero"] = {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            }
        bubbles.append(bubble)

    messages = []
    if text:
        messages.append(_text_msg(text))
    messages.append({
        "type": "flex",
        "altText": f"{restaurant_name} menu — {len(bubbles)} item(s)",
        "contents": {"type": "carousel", "contents": bubbles},
    })
    return messages


def _handle_add_to_cart(text: str, data: dict) -> list[dict]:
    """Cart update → text summary."""
    added = data.get("added", {})
    total = data.get("total", 0)
    cart_count = data.get("cart_count", 0)

    if text:
        return [_text_msg(text)]

    name = added.get("name", "item")
    return [_text_msg(f"Added {name} to cart. {cart_count} item(s), total: ${total:.2f}")]


def _handle_get_order_summary(text: str, data: dict) -> list[dict]:
    """Order summary → Flex Bubble with itemized list."""
    items = data.get("items", [])
    subtotal = data.get("subtotal", 0)
    delivery_fee = data.get("delivery_fee", 0)
    total = data.get("total", 0)
    restaurant_name = data.get("restaurant_name", "")
    delivery_min = data.get("estimated_delivery_min", 0)
    payment_options = data.get("payment_options", [])

    item_rows: list[dict] = []
    for item in items:
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        name = item.get("name", "")
        special = item.get("special_requests", "")
        label = f"{name} x{qty}"
        if special:
            label += f" ({special})"
        item_rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": label, "size": "sm", "flex": 3, "wrap": True},
                {"type": "text", "text": f"${price * qty:.2f}", "size": "sm", "align": "end", "flex": 1},
            ],
        })

    body_contents: list[dict] = [
        {"type": "text", "text": "\U0001f4cb Order Summary", "weight": "bold", "size": "lg"},
    ]
    if restaurant_name:
        body_contents.append({"type": "text", "text": f"\U0001f3ea {restaurant_name}", "size": "sm", "color": "#555555"})
    body_contents.append({"type": "separator", "margin": "md"})
    body_contents.extend(item_rows)
    body_contents.append({"type": "separator", "margin": "md"})
    body_contents.append({
        "type": "box", "layout": "horizontal", "margin": "sm",
        "contents": [
            {"type": "text", "text": "Subtotal", "size": "sm", "color": "#999999"},
            {"type": "text", "text": f"${subtotal:.2f}", "size": "sm", "align": "end"},
        ],
    })
    body_contents.append({
        "type": "box", "layout": "horizontal",
        "contents": [
            {"type": "text", "text": "Delivery", "size": "sm", "color": "#999999"},
            {"type": "text", "text": f"${delivery_fee:.2f}", "size": "sm", "align": "end"},
        ],
    })
    body_contents.append({"type": "separator", "margin": "sm"})
    body_contents.append({
        "type": "box", "layout": "horizontal", "margin": "md",
        "contents": [
            {"type": "text", "text": "Total", "weight": "bold", "size": "md"},
            {"type": "text", "text": f"${total:.2f}", "weight": "bold", "size": "lg", "color": "#E74C3C", "align": "end"},
        ],
    })
    if delivery_min:
        body_contents.append({"type": "text", "text": f"\U0001f6b4 Est. {delivery_min} min", "size": "xs", "color": "#888888", "margin": "sm"})

    footer_buttons: list[dict] = [
        {
            "type": "button",
            "action": {"type": "message", "label": "\u2705 Confirm Order", "text": "Yes"},
            "style": "primary",
            "color": "#27AE60",
            "height": "sm",
        },
        {
            "type": "button",
            "action": {"type": "message", "label": "\u270f\ufe0f Modify", "text": "I want to change my order"},
            "style": "secondary",
            "height": "sm",
        },
    ]

    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body_contents},
        "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer_buttons},
    }

    messages = []
    if text:
        messages.append(_text_msg(text))
    messages.append({
        "type": "flex",
        "altText": f"Order summary — ${total:.2f}",
        "contents": bubble,
    })
    return messages


def _handle_initiate_payment(text: str, data: dict) -> list[dict]:
    """Payment initiation → text (suggested_replies will show payment options)."""
    return [_text_msg(text)] if text else []


def _handle_confirm_payment(text: str, data: dict) -> list[dict]:
    """Payment confirmed → Flex Bubble confirmation card."""
    order_id = data.get("order_id", "")
    amount = data.get("amount_charged", 0)
    payment_method = data.get("payment_method", "")
    restaurant_name = data.get("restaurant_name", "")
    delivery_min = data.get("estimated_delivery_min", 0)

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": "\u2705 Payment Confirmed!", "weight": "bold", "size": "lg", "color": "#27AE60"},
                {"type": "text", "text": f"\U0001f4e6 {order_id}", "size": "sm", "color": "#888888"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"\U0001f3ea {restaurant_name}", "size": "sm", "margin": "md"},
                {
                    "type": "box", "layout": "horizontal", "margin": "sm",
                    "contents": [
                        {"type": "text", "text": "Paid", "size": "sm", "color": "#999999"},
                        {"type": "text", "text": f"${amount:.2f}", "size": "sm", "weight": "bold", "align": "end"},
                    ],
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "Method", "size": "sm", "color": "#999999"},
                        {"type": "text", "text": payment_method.replace("_", " ").title(), "size": "sm", "align": "end"},
                    ],
                },
                {"type": "text", "text": f"\U0001f6b4 Est. {delivery_min} min delivery", "size": "xs", "color": "#888888", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "message", "label": "\U0001f4e6 Track Order", "text": "Track my order"},
                    "style": "primary",
                    "color": "#3498DB",
                    "height": "sm",
                },
            ],
        },
    }

    messages = []
    if text:
        messages.append(_text_msg(text))
    messages.append({
        "type": "flex",
        "altText": f"Payment confirmed — {order_id}",
        "contents": bubble,
    })
    return messages


def _handle_get_order_status(text: str, data: dict) -> list[dict]:
    """Order status → Flex Bubble with timeline."""
    order_id = data.get("order_id", "")
    status = data.get("status", "")
    restaurant_name = data.get("restaurant_name", "")
    delivery_min = data.get("estimated_delivery_min", 0)
    timeline = data.get("timeline", [])

    timeline_rows: list[dict] = []
    for step in timeline:
        completed = step.get("completed", False)
        icon = "\u2705" if completed else "\u26aa"
        color = "#27AE60" if completed else "#CCCCCC"
        timeline_rows.append({
            "type": "text",
            "text": f"{icon} {step.get('label', '')}",
            "size": "sm",
            "color": color,
        })

    body = [
        {"type": "text", "text": "\U0001f4e6 Order Status", "weight": "bold", "size": "lg"},
        {"type": "text", "text": f"{order_id} · {restaurant_name}", "size": "xs", "color": "#888888"},
        {"type": "separator", "margin": "md"},
        *timeline_rows,
    ]
    if delivery_min:
        body.append({"type": "text", "text": f"\U0001f552 Est. {delivery_min} min", "size": "xs", "color": "#888888", "margin": "md"})

    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": body},
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "\U0001f4cd Track Rider", "text": "Track rider"}, "style": "primary", "color": "#3498DB", "height": "sm"},
            ],
        },
    }

    messages = []
    if text:
        messages.append(_text_msg(text))
    messages.append({"type": "flex", "altText": f"Order {order_id} — {status}", "contents": bubble})
    return messages


def _handle_track_rider(text: str, data: dict) -> list[dict]:
    """Rider tracking → text with location info."""
    rider = data.get("rider", {})
    eta = data.get("estimated_arrival_min", 0)
    distance = data.get("distance_km", 0)
    rider_name = rider.get("name", "Rider")

    if text:
        return [_text_msg(text)]
    return [_text_msg(f"\U0001f6f5 {rider_name} is on the way! {distance} km away, arriving in ~{eta} min.")]


def _handle_submit_review(text: str, data: dict) -> list[dict]:
    """Review submitted → text confirmation."""
    return [_text_msg(text)] if text else []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HANDLER REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_TOOL_HANDLERS: dict[str, Any] = {
    "get_food_categories": _handle_get_food_categories,
    "search_restaurants": _handle_search_restaurants,
    "get_restaurant_menu": _handle_get_restaurant_menu,
    "add_to_cart": _handle_add_to_cart,
    "get_order_summary": _handle_get_order_summary,
    "place_order": lambda text, data: [_text_msg(text)] if text else [],
    "initiate_payment": _handle_initiate_payment,
    "confirm_payment": _handle_confirm_payment,
    "get_order_status": _handle_get_order_status,
    "track_rider": _handle_track_rider,
    "submit_review": _handle_submit_review,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _strip_markdown(text: str) -> str:
    """Strip Markdown formatting that LINE cannot render."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold**
    text = re.sub(r'__(.+?)__', r'\1', text)        # __bold__
    text = re.sub(r'\*(.+?)\*', r'\1', text)        # *italic*
    text = re.sub(r'_(.+?)_', r'\1', text)          # _italic_
    text = re.sub(r'~~(.+?)~~', r'\1', text)        # ~~strikethrough~~
    text = re.sub(r'`(.+?)`', r'\1', text)          # `code`
    return text


def _text_msg(text: str) -> dict:
    return {"type": "text", "text": _strip_markdown(text)}


def _safe_parse(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _attach_quick_reply(message: dict, options: list[str]) -> None:
    """Attach suggested_replies as LINE Quick Reply items to a message."""
    items = []
    for option in options[:13]:  # LINE max 13 quick reply items
        items.append({
            "type": "action",
            "action": {
                "type": "message",
                "label": option[:20],  # LINE max label 20 chars
                "text": option,
            },
        })
    if items:
        message["quickReply"] = {"items": items}
