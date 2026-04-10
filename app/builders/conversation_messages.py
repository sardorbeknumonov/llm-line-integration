"""LINE message builders for each step of the food ordering conversation.

Every function returns list[dict] — LINE message objects ready for reply/push.
All interactive elements use `type: "message"` so tapped text flows back to the webhook.
"""

from __future__ import annotations

from app.models.menu import Restaurant, MenuItem
from app.data.static_menu import CATEGORIES, get_restaurants


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _quick_replies(options: list[str]) -> dict:
    """Build a quickReply object from a list of option strings."""
    return {
        "items": [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": opt[:20],
                    "text": opt,
                },
            }
            for opt in options[:13]
        ]
    }


def _star_display(rating: float) -> str:
    full = int(rating)
    half = "\u00bd" if rating - full >= 0.5 else ""
    return "\u2b50" * full + half


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 1 — GREETING & FOOD SELECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_greeting() -> list[dict]:
    """Greeting + category quick replies."""
    return [{
        "type": "text",
        "text": (
            "\U0001f44b Hi there! Happy to help you get food "
            "delivered right to your door. \U0001f60a\n\n"
            "What are you in the mood for today?"
        ),
        "quickReply": _quick_replies([c["label"] for c in CATEGORIES]),
    }]


def build_restaurant_list(category_key: str) -> list[dict]:
    """Flex carousel of restaurants for a category + quick replies to select."""
    restaurants = get_restaurants(category_key)
    if not restaurants:
        return [{"type": "text", "text": "Sorry, no restaurants found for that category."}]

    # Build carousel bubbles
    bubbles = []
    for r in restaurants:
        bubbles.append(_build_restaurant_bubble(r))

    # Header text
    category_label = next(
        (c["label"] for c in CATEGORIES if c["key"] == category_key), category_key
    )
    header = f"Great choice! {category_label} Here are top restaurants near you:"

    # Quick reply options with restaurant names
    qr_options = [r.name for r in restaurants]

    messages = [
        {"type": "text", "text": header},
        {
            "type": "flex",
            "altText": f"{category_label} restaurants",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
    # Add quick replies to the last message
    messages[-1]["quickReply"] = _quick_replies(qr_options)
    return messages


def _build_restaurant_bubble(r: Restaurant) -> dict:
    """Build a Flex Bubble for a restaurant card."""
    bubble: dict = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": r.name,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": f"{_star_display(r.rating)} {r.rating}",
                    "size": "sm",
                    "color": "#FFB800",
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "md",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"\U0001f559 {r.delivery_time_min} min",
                            "size": "xs",
                            "color": "#888888",
                            "flex": 1,
                        },
                        {
                            "type": "text",
                            "text": f"\U0001f4b0 From ${r.price_from:.2f}",
                            "size": "xs",
                            "color": "#888888",
                            "flex": 1,
                        },
                    ],
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "\U0001f4d6 View Menu",
                        "text": r.name,
                    },
                    "style": "primary",
                    "color": "#FF6B35",
                    "height": "sm",
                },
            ],
        },
    }
    if r.image_url:
        bubble["hero"] = {
            "type": "image",
            "url": r.image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        }
    return bubble


def build_menu_items(restaurant: Restaurant) -> list[dict]:
    """Flex carousel of menu items for a restaurant."""
    bubbles = []
    for item in restaurant.menu:
        bubbles.append(_build_menu_item_bubble(item, restaurant.name))

    qr_options = [item.name for item in restaurant.menu] + ["\U0001f4d6 See Full Menu"]

    messages = [
        {
            "type": "text",
            "text": f"Here are the most popular items at {restaurant.name} \U0001f962",
        },
        {
            "type": "flex",
            "altText": f"Menu - {restaurant.name}",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
    messages[-1]["quickReply"] = _quick_replies(qr_options)
    return messages


def _build_menu_item_bubble(item: MenuItem, restaurant_name: str) -> dict:
    """Build a Flex Bubble for a single menu item."""
    bubble: dict = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": item.name,
                    "weight": "bold",
                    "size": "md",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": item.description,
                    "size": "xs",
                    "color": "#888888",
                    "wrap": True,
                    "maxLines": 2,
                },
                {"type": "separator", "margin": "lg"},
                {
                    "type": "text",
                    "text": f"${item.price:.2f}",
                    "size": "xl",
                    "weight": "bold",
                    "color": "#E74C3C",
                    "margin": "md",
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": f"\U0001f6d2 Order — ${item.price:.2f}",
                        "text": item.name,
                    },
                    "style": "primary",
                    "color": "#E74C3C",
                    "height": "sm",
                },
            ],
        },
    }
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
#  SPECIAL REQUEST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_special_request_prompt(item_name: str) -> list[dict]:
    return [{
        "type": "text",
        "text": (
            f"Got it! \U0001f35c {item_name}\n\n"
            "Any special requests?\n"
            "(e.g., no green onions, extra spicy, less soup)"
        ),
        "quickReply": _quick_replies(["No, I'm good!", "Add a note"]),
    }]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 2 — ORDER SUMMARY & PAYMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DELIVERY_FEE = 2.50
DEFAULT_ADDRESS = "Margaret's Home (saved address)"


def build_order_summary(
    item: MenuItem,
    restaurant_name: str,
    address: str = DEFAULT_ADDRESS,
    special_note: str = "",
) -> list[dict]:
    """Order summary Flex Bubble with Confirm/Cancel/Change Address."""
    total = item.price + DELIVERY_FEE

    body_contents = [
        {
            "type": "text",
            "text": "\U0001f4cb Order Summary",
            "weight": "bold",
            "size": "lg",
        },
        {"type": "separator", "margin": "md"},
        # Item row
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f"\U0001f35c {item.name} \u00d7 1",
                    "size": "sm",
                    "flex": 3,
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": f"${item.price:.2f}",
                    "size": "sm",
                    "align": "end",
                    "flex": 1,
                },
            ],
        },
        # Delivery fee
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "\U0001f6f5 Delivery fee", "size": "sm", "flex": 3, "color": "#888888"},
                {"type": "text", "text": f"${DELIVERY_FEE:.2f}", "size": "sm", "align": "end", "flex": 1, "color": "#888888"},
            ],
        },
        {"type": "separator", "margin": "md"},
        # Total
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {"type": "text", "text": "\U0001f4b0 Total:", "weight": "bold", "size": "md"},
                {
                    "type": "text",
                    "text": f"${total:.2f}",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#E74C3C",
                    "align": "end",
                },
            ],
        },
        {"type": "separator", "margin": "md"},
        # Address
        {
            "type": "text",
            "text": f"\U0001f4cd {address}",
            "size": "xs",
            "color": "#555555",
            "margin": "md",
            "wrap": True,
        },
        # Estimated arrival
        {
            "type": "text",
            "text": "\U0001f559 Estimated arrival: ~20 minutes",
            "size": "xs",
            "color": "#555555",
        },
    ]

    if special_note:
        body_contents.append({
            "type": "text",
            "text": f"\U0001f4dd Note: {special_note}",
            "size": "xs",
            "color": "#555555",
            "wrap": True,
            "margin": "sm",
        })

    bubble = {
        "type": "bubble",
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
                    "action": {"type": "message", "label": "\u2705 Confirm Order", "text": "\u2705 Confirm Order"},
                    "style": "primary",
                    "color": "#27AE60",
                    "height": "sm",
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "\u274c Cancel", "text": "\u274c Cancel"},
                            "style": "secondary",
                            "height": "sm",
                            "flex": 1,
                        },
                        {
                            "type": "button",
                            "action": {"type": "message", "label": "\u270f\ufe0f Change Address", "text": "\u270f\ufe0f Change Address"},
                            "style": "secondary",
                            "height": "sm",
                            "flex": 1,
                        },
                    ],
                },
            ],
        },
    }

    return [{
        "type": "flex",
        "altText": "Order Summary",
        "contents": bubble,
    }]


def build_payment_options() -> list[dict]:
    return [{
        "type": "text",
        "text": "Almost there! How would you like to pay?",
        "quickReply": _quick_replies([
            "\U0001f49a LINE Pay",
            "\U0001f4b5 Cash on Delivery",
            "\U0001f4b3 Credit Card",
        ]),
    }]


def build_payment_success(method: str, order_id: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": (
                f"\u2705 Payment successful! {method}\n\n"
                f"\U0001f4e6 Order ID: {order_id}\n\n"
                "\U0001f389 Your order has been sent to the restaurant. Sit tight!"
            ),
        },
    ]


def build_address_prompt() -> list[dict]:
    return [{"type": "text", "text": "\U0001f4cd Please type your new delivery address:"}]


def build_order_cancelled() -> list[dict]:
    return [{
        "type": "text",
        "text": (
            "\u274c Order cancelled.\n\n"
            "No worries! Type 'Hello' whenever you're ready to order again. \U0001f60a"
        ),
    }]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 3 — DELIVERY TRACKING (proactive push)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_tracking_preparing(restaurant_name: str) -> list[dict]:
    return [{
        "type": "text",
        "text": (
            f"\U0001f514 Order Update!\n\n"
            f"\u2705 {restaurant_name} has accepted your order and is "
            f"preparing your food! \U0001f35c"
        ),
    }]


def build_tracking_rider() -> list[dict]:
    return [{
        "type": "text",
        "text": (
            "\U0001f6f5 Your rider is on the way!\n\n"
            "James has picked up your food and is heading to you now.\n"
            "\U0001f559 Estimated arrival: ~8 minutes"
        ),
        "quickReply": _quick_replies(["\U0001f4cd Track My Rider"]),
    }]


def build_tracking_map() -> list[dict]:
    """Simulated map response when user taps Track My Rider."""
    return [{
        "type": "text",
        "text": (
            "\U0001f4cd Live Tracking\n\n"
            "\U0001f6f5 James is 0.8 km away\n"
            "\U0001f559 Arriving in ~5 minutes\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u25cf\u2501\u2501\u2501 80%\n"
            "Restaurant \u2192 \U0001f3e0 You"
        ),
    }]


def build_tracking_delivered() -> list[dict]:
    return [{
        "type": "text",
        "text": "\U0001f389 Order delivered! Enjoy your meal! \U0001f35c\U0001f60a",
    }]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACT 4 — REVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_review_rating_prompt() -> list[dict]:
    return [{
        "type": "text",
        "text": "How was your food? Your review helps others find great restaurants! \u2b50",
        "quickReply": _quick_replies([
            "\u2b50",
            "\u2b50\u2b50",
            "\u2b50\u2b50\u2b50",
            "\u2b50\u2b50\u2b50\u2b50",
            "\u2b50\u2b50\u2b50\u2b50\u2b50",
        ]),
    }]


def build_review_highlights_prompt(rating: int) -> list[dict]:
    stars = "\u2b50" * rating
    return [{
        "type": "text",
        "text": f"\U0001f31f {stars} Wonderful! Anything you'd like to highlight?",
        "quickReply": _quick_replies([
            "\U0001f60b Delicious!",
            "\u26a1 Super fast",
            "\U0001f44d Great portion",
            "\u270f\ufe0f Write my own",
        ]),
    }]


def build_review_custom_prompt() -> list[dict]:
    return [{"type": "text", "text": "Please type your review:"}]


def build_review_complete() -> list[dict]:
    return [{
        "type": "text",
        "text": (
            "\u2705 Review saved \u2014 thank you! \U0001f64f\n\n"
            "Come back anytime you're hungry! "
            "We're always here in your LINE chat! \U0001f60a"
        ),
        "quickReply": _quick_replies([
            "\U0001f37d\ufe0f Order Again",
            "\U0001f4cb View Order History",
        ]),
    }]


def build_order_history(order_id: str, item_name: str, total: float) -> list[dict]:
    return [{
        "type": "text",
        "text": (
            "\U0001f4cb Order History\n\n"
            f"\U0001f4e6 {order_id}\n"
            f"\U0001f35c {item_name}\n"
            f"\U0001f4b0 ${total:.2f}\n"
            "\u2705 Delivered\n\n"
            "Type 'Hello' to order again!"
        ),
    }]
