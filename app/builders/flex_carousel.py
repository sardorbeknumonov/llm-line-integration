"""Build LINE Flex Message carousels and bubbles for food ordering.

In the middleware architecture, button actions use LINE `message` type
(not postback) so the user's tap text gets forwarded to Sendbird AI Agent.
"""

from __future__ import annotations

from app.models.messages import FoodItemData, OrderConfirmationData, ButtonsData


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _star_rating(rating: float) -> str:
    full = int(rating)
    half = "\u00bd" if rating - full >= 0.5 else ""
    empty = 5 - full - (1 if half else 0)
    return "\u2605" * full + half + "\u2606" * empty


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SINGLE FOOD BUBBLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_food_bubble(item: FoodItemData) -> dict:
    """
    Build one Flex Bubble for a food item.

    ┌──────────────────────────┐
    │      FOOD IMAGE          │
    ├──────────────────────────┤
    │ Food Name (bold)         │
    │ 🏪 Restaurant            │
    │ ★★★★½ 4.8               │
    │ 🚴 25 min delivery       │
    │ ──────────────────────── │
    │ Price          $15.99    │
    ├──────────────────────────┤
    │  [ 🛒 Order           ]  │
    │  [➕ Add to Cart      ]  │
    │  [📋 Details          ]  │
    └──────────────────────────┘

    Buttons use `message` action type so the text is sent back
    to LINE chat → forwarded to Sendbird AI Agent.
    """
    body_contents: list[dict] = [
        # Food name
        {
            "type": "text",
            "text": item.name,
            "weight": "bold",
            "size": "lg",
            "wrap": True,
            "maxLines": 2,
        },
    ]

    # Restaurant
    if item.restaurant:
        body_contents.append({
            "type": "text",
            "text": f"\U0001f3ea {item.restaurant}",
            "size": "sm",
            "color": "#555555",
        })

    # Rating
    if item.rating > 0:
        body_contents.append({
            "type": "text",
            "text": f"{_star_rating(item.rating)} {item.rating}",
            "size": "xs",
            "color": "#FFB800",
        })

    # Delivery time
    if item.delivery_time_min > 0:
        body_contents.append({
            "type": "text",
            "text": f"\U0001f6b4 {item.delivery_time_min} min delivery",
            "size": "xs",
            "color": "#888888",
            "margin": "sm",
        })

    # Separator + Price
    if item.price > 0:
        body_contents.append({"type": "separator", "margin": "lg"})
        body_contents.append({
            "type": "box",
            "layout": "horizontal",
            "margin": "lg",
            "contents": [
                {"type": "text", "text": "Price", "size": "sm", "color": "#999999"},
                {
                    "type": "text",
                    "text": f"${item.price:.2f}",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#E74C3C",
                    "align": "end",
                },
            ],
        })

    # Build bubble
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
                # 🛒 Order
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "\U0001f6d2 Order",
                        "text": f"Order {item.name}" + (f" from {item.restaurant}" if item.restaurant else ""),
                    },
                    "style": "primary",
                    "color": "#E74C3C",
                    "height": "sm",
                },
                # ➕ Add to Cart
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "\u2795 Add to Cart",
                        "text": f"Add {item.name} to cart",
                    },
                    "style": "secondary",
                    "height": "sm",
                },
                # 📋 Details
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "\U0001f4cb Details",
                        "text": f"Tell me more about {item.name}",
                    },
                    "style": "link",
                    "height": "sm",
                },
            ],
        },
    }

    # Add hero image if URL provided
    if item.image_url:
        bubble["hero"] = {
            "type": "image",
            "url": item.image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        }

    return bubble


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FOOD CAROUSEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_food_carousel(items: list[FoodItemData]) -> dict:
    """Build a Flex Carousel from food items (max 12)."""
    return {
        "type": "carousel",
        "contents": [build_food_bubble(item) for item in items[:12]],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ORDER CONFIRMATION BUBBLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_order_confirmation_bubble(order: OrderConfirmationData) -> dict:
    """Build order confirmation Flex Bubble."""
    item_rows: list[dict] = []
    for item in order.items:
        item_rows.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": f"{item.name} x{item.qty}",
                    "size": "sm",
                    "flex": 3,
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": f"${item.price * item.qty:.2f}",
                    "size": "sm",
                    "align": "end",
                    "flex": 1,
                },
            ],
        })

    status_color = {
        "confirmed": "#27AE60",
        "preparing": "#F39C12",
        "delivering": "#3498DB",
        "delivered": "#27AE60",
    }.get(order.status, "#555555")

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": "\U0001f389 Order Confirmed!",
                    "weight": "bold",
                    "size": "lg",
                },
                {
                    "type": "text",
                    "text": f"\U0001f4e6 {order.order_id}",
                    "size": "sm",
                    "color": "#888888",
                },
                {
                    "type": "text",
                    "text": order.status.upper(),
                    "size": "xs",
                    "color": status_color,
                    "weight": "bold",
                },
                {"type": "separator", "margin": "md"},
                *item_rows,
                {"type": "separator", "margin": "md"},
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "Total", "weight": "bold", "size": "md"},
                        {
                            "type": "text",
                            "text": f"${order.total:.2f}",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#E74C3C",
                            "align": "end",
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": f"\U0001f6b4 Est. {order.delivery_min} min",
                    "size": "xs",
                    "color": "#888888",
                    "margin": "sm",
                },
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
                        "label": "\U0001f4e6 Track Order",
                        "text": f"Track order {order.order_id}",
                    },
                    "style": "primary",
                    "color": "#3498DB",
                    "height": "sm",
                },
            ],
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUTTONS BUBBLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_buttons_bubble(data: ButtonsData) -> dict:
    """Build a Flex Bubble with title, text, and action buttons."""
    body_contents: list[dict] = []

    if data.title:
        body_contents.append({
            "type": "text",
            "text": data.title,
            "weight": "bold",
            "size": "lg",
            "wrap": True,
        })
    if data.text:
        body_contents.append({
            "type": "text",
            "text": data.text,
            "size": "sm",
            "color": "#555555",
            "wrap": True,
            "margin": "md",
        })

    button_list: list[dict] = []
    colors = ["#E74C3C", "#3498DB", "#27AE60", "#F39C12"]
    for i, action in enumerate(data.actions[:4]):
        button_list.append({
            "type": "button",
            "action": {
                "type": "message",
                "label": action.label[:20],  # LINE max label 20 chars
                "text": action.text,
            },
            "style": "primary" if i == 0 else "secondary",
            "color": colors[i % len(colors)] if i == 0 else None,
            "height": "sm",
        })
        # Remove None color for secondary buttons
        if button_list[-1]["color"] is None:
            del button_list[-1]["color"]

    bubble: dict = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": body_contents or [{"type": "text", "text": " "}],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": button_list,
        },
    }

    if data.image_url:
        bubble["hero"] = {
            "type": "image",
            "url": data.image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        }

    return bubble
