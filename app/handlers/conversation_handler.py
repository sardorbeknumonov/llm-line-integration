"""Conversation state machine — routes user input to the correct response.

Manages per-user sessions in-memory. Each user has a state and context data
that tracks their progress through the ordering flow.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto

from app.models.menu import MenuItem, Restaurant
from app.services.line_client import LineClient
from app.utils.text_matching import is_greeting, fuzzy_match
from app.data.static_menu import (
    CATEGORY_LABELS,
    resolve_category_key,
    get_restaurants,
    find_restaurant,
    find_menu_item,
)
from app.builders.conversation_messages import (
    build_greeting,
    build_restaurant_list,
    build_menu_items,
    build_special_request_prompt,
    build_order_summary,
    build_payment_options,
    build_payment_success,
    build_address_prompt,
    build_order_cancelled,
    build_tracking_map,
    build_review_rating_prompt,
    build_review_highlights_prompt,
    build_review_custom_prompt,
    build_review_complete,
    build_order_history,
    DEFAULT_ADDRESS,
    DELIVERY_FEE,
)

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class State(Enum):
    IDLE = auto()
    CATEGORY_SELECTION = auto()
    RESTAURANT_SELECTION = auto()
    MENU_SELECTION = auto()
    SPECIAL_REQUEST = auto()
    ADDING_NOTE = auto()
    ORDER_SUMMARY = auto()
    ADDRESS_CHANGE = auto()
    PAYMENT_SELECTION = auto()
    TRACKING = auto()
    REVIEW_RATING = auto()
    REVIEW_HIGHLIGHTS = auto()
    REVIEW_CUSTOM_TEXT = auto()
    REVIEW_COMPLETE = auto()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class UserSession:
    state: State = State.IDLE
    category_key: str | None = None
    restaurant: Restaurant | None = None
    selected_item: MenuItem | None = None
    special_note: str = ""
    address: str = DEFAULT_ADDRESS
    order_id: str = ""
    payment_method: str = ""
    rating: int = 0
    highlights: list[str] = field(default_factory=list)
    delivery_task: asyncio.Task | None = field(default=None, repr=False)


# In-memory session store
_sessions: dict[str, UserSession] = {}


def get_session(user_id: str) -> UserSession:
    if user_id not in _sessions:
        _sessions[user_id] = UserSession()
    return _sessions[user_id]


def reset_session(user_id: str) -> UserSession:
    old = _sessions.get(user_id)
    if old and old.delivery_task and not old.delivery_task.done():
        old.delivery_task.cancel()
    _sessions[user_id] = UserSession()
    return _sessions[user_id]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_conversation(
    line: LineClient,
    user_id: str,
    reply_token: str,
    text: str,
) -> None:
    """Route user text through the FSM and reply with the appropriate message."""
    session = get_session(user_id)

    # Escape hatch: greeting at any state restarts
    if is_greeting(text) and session.state != State.CATEGORY_SELECTION:
        session = reset_session(user_id)
        session.state = State.CATEGORY_SELECTION
        await line.reply(reply_token, build_greeting())
        return

    # Dispatch to state handler
    handler = _STATE_HANDLERS.get(session.state, _handle_idle)
    messages = await handler(session, user_id, text, line)

    if messages:
        await line.reply(reply_token, messages)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATE HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _handle_idle(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """IDLE → greeting → CATEGORY_SELECTION."""
    session.state = State.CATEGORY_SELECTION
    return build_greeting()


async def _handle_category_selection(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """CATEGORY_SELECTION → tap category → RESTAURANT_SELECTION."""
    category_key = resolve_category_key(text)
    if not category_key:
        return [{
            "type": "text",
            "text": "Hmm, I didn't catch that. Please pick a category:",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": c[:20], "text": c}}
                    for c in CATEGORY_LABELS
                ]
            },
        }]

    session.category_key = category_key
    session.state = State.RESTAURANT_SELECTION
    return build_restaurant_list(category_key)


async def _handle_restaurant_selection(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """RESTAURANT_SELECTION → tap restaurant → MENU_SELECTION."""
    restaurant = find_restaurant(text, session.category_key)
    if not restaurant:
        restaurants = get_restaurants(session.category_key or "")
        return [{
            "type": "text",
            "text": "I didn't find that restaurant. Please tap one from the list:",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": r.name[:20], "text": r.name}}
                    for r in restaurants
                ]
            },
        }]

    session.restaurant = restaurant
    session.state = State.MENU_SELECTION
    return build_menu_items(restaurant)


async def _handle_menu_selection(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """MENU_SELECTION → tap item → SPECIAL_REQUEST."""
    if not session.restaurant:
        session.state = State.CATEGORY_SELECTION
        return build_greeting()

    item = find_menu_item(text, session.restaurant)
    if not item:
        return [{
            "type": "text",
            "text": "I didn't find that item. Please pick from the menu:",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": i.name[:20], "text": i.name}}
                    for i in session.restaurant.menu
                ]
            },
        }]

    session.selected_item = item
    session.state = State.SPECIAL_REQUEST
    return build_special_request_prompt(item.name)


async def _handle_special_request(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """SPECIAL_REQUEST → confirm or add note → ORDER_SUMMARY."""
    normalized = text.strip().lower()

    if "add a note" in normalized or "note" == normalized:
        session.state = State.ADDING_NOTE
        return [{"type": "text", "text": "\U0001f4dd Please type your special request:"}]

    # "No, I'm good!" or anything else → proceed
    if "no" in normalized or "good" in normalized or "i'm good" in normalized:
        session.special_note = ""
    else:
        # User typed a note directly
        session.special_note = text.strip()

    session.state = State.ORDER_SUMMARY
    return build_order_summary(
        session.selected_item,
        session.restaurant.name if session.restaurant else "",
        session.address,
        session.special_note,
    )


async def _handle_adding_note(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """ADDING_NOTE → user types note → ORDER_SUMMARY."""
    session.special_note = text.strip()
    session.state = State.ORDER_SUMMARY
    return build_order_summary(
        session.selected_item,
        session.restaurant.name if session.restaurant else "",
        session.address,
        session.special_note,
    )


async def _handle_order_summary(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """ORDER_SUMMARY → Confirm / Cancel / Change Address."""
    normalized = text.strip().lower()

    if "confirm" in normalized:
        session.state = State.PAYMENT_SELECTION
        return build_payment_options()
    elif "cancel" in normalized:
        reset_session(user_id)
        return build_order_cancelled()
    elif "change address" in normalized or "address" in normalized:
        session.state = State.ADDRESS_CHANGE
        return build_address_prompt()
    else:
        return [{"type": "text", "text": "Please tap Confirm, Cancel, or Change Address."}]


async def _handle_address_change(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """ADDRESS_CHANGE → user types address → ORDER_SUMMARY."""
    session.address = text.strip()
    session.state = State.ORDER_SUMMARY
    return build_order_summary(
        session.selected_item,
        session.restaurant.name if session.restaurant else "",
        session.address,
        session.special_note,
    )


async def _handle_payment_selection(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """PAYMENT_SELECTION → tap method → start delivery tracking."""
    payment_methods = ["\U0001f49a LINE Pay", "\U0001f4b5 Cash on Delivery", "\U0001f4b3 Credit Card"]
    matched = fuzzy_match(text, payment_methods)

    if not matched:
        return [{
            "type": "text",
            "text": "Please select a payment method:",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": m[:20], "text": m}}
                    for m in payment_methods
                ]
            },
        }]

    session.payment_method = matched
    session.order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    session.state = State.TRACKING

    # Start delivery simulation in background
    from app.services.delivery_tracker import simulate_delivery
    session.delivery_task = asyncio.create_task(
        simulate_delivery(line, user_id, session)
    )

    return build_payment_success(matched, session.order_id)


async def _handle_tracking(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """TRACKING — user taps Track My Rider."""
    if "track" in text.lower():
        return build_tracking_map()
    return [{"type": "text", "text": "\U0001f6f5 Your order is on the way! Hang tight."}]


async def _handle_review_rating(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """REVIEW_RATING → tap stars → REVIEW_HIGHLIGHTS."""
    # Count stars
    star_count = text.count("\u2b50")
    if star_count == 0:
        # Try numeric
        try:
            star_count = int(text.strip())
        except ValueError:
            pass

    if star_count < 1 or star_count > 5:
        return build_review_rating_prompt()

    session.rating = star_count
    session.state = State.REVIEW_HIGHLIGHTS
    return build_review_highlights_prompt(star_count)


async def _handle_review_highlights(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """REVIEW_HIGHLIGHTS → tap highlight or write own."""
    if "write my own" in text.lower() or "write" in text.lower():
        session.state = State.REVIEW_CUSTOM_TEXT
        return build_review_custom_prompt()

    session.highlights.append(text.strip())
    session.state = State.REVIEW_COMPLETE
    return build_review_complete()


async def _handle_review_custom_text(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """REVIEW_CUSTOM_TEXT → user types review → REVIEW_COMPLETE."""
    session.highlights.append(text.strip())
    session.state = State.REVIEW_COMPLETE
    return build_review_complete()


async def _handle_review_complete(
    session: UserSession, user_id: str, text: str, line: LineClient
) -> list[dict]:
    """REVIEW_COMPLETE → Order Again or View History."""
    if "order again" in text.lower() or "order" in text.lower():
        session.state = State.CATEGORY_SELECTION
        return build_greeting()
    elif "history" in text.lower():
        total = (session.selected_item.price + DELIVERY_FEE) if session.selected_item else 0
        item_name = session.selected_item.name if session.selected_item else "Unknown"
        msgs = build_order_history(session.order_id, item_name, total)
        reset_session(user_id)
        return msgs
    else:
        return build_review_complete()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HANDLER REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_STATE_HANDLERS = {
    State.IDLE: _handle_idle,
    State.CATEGORY_SELECTION: _handle_category_selection,
    State.RESTAURANT_SELECTION: _handle_restaurant_selection,
    State.MENU_SELECTION: _handle_menu_selection,
    State.SPECIAL_REQUEST: _handle_special_request,
    State.ADDING_NOTE: _handle_adding_note,
    State.ORDER_SUMMARY: _handle_order_summary,
    State.ADDRESS_CHANGE: _handle_address_change,
    State.PAYMENT_SELECTION: _handle_payment_selection,
    State.TRACKING: _handle_tracking,
    State.REVIEW_RATING: _handle_review_rating,
    State.REVIEW_HIGHLIGHTS: _handle_review_highlights,
    State.REVIEW_CUSTOM_TEXT: _handle_review_custom_text,
    State.REVIEW_COMPLETE: _handle_review_complete,
}
