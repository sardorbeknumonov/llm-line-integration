"""Message models for structured AI Agent responses.

The Sendbird AI Agent can include a `data` field (JSON string) on its messages.
These models represent the parsed structure for rich LINE rendering.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FOOD CAROUSEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FoodItemData(BaseModel):
    """A single food item from the AI Agent's structured response."""
    food_id: str = ""
    name: str
    restaurant: str = ""
    price: float = 0.0
    image_url: str = ""
    rating: float = 0.0
    description: str = ""
    delivery_time_min: int = 30


class FoodCarouselData(BaseModel):
    """data.type == 'food_carousel'"""
    type: str = "food_carousel"
    items: list[FoodItemData]
    header_text: str = ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ORDER CONFIRMATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OrderItemData(BaseModel):
    name: str
    qty: int = 1
    price: float = 0.0


class OrderConfirmationData(BaseModel):
    """data.type == 'order_confirmation'"""
    type: str = "order_confirmation"
    order_id: str = ""
    items: list[OrderItemData] = Field(default_factory=list)
    total: float = 0.0
    delivery_min: int = 30
    status: str = "confirmed"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUTTONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ButtonAction(BaseModel):
    label: str
    text: str  # message text sent back to chat when tapped


class ButtonsData(BaseModel):
    """data.type == 'buttons'"""
    type: str = "buttons"
    title: str = ""
    text: str = ""
    image_url: str = ""
    actions: list[ButtonAction] = Field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  QUICK REPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QuickReplyData(BaseModel):
    """data.type == 'quick_reply'"""
    type: str = "quick_reply"
    text: str = ""
    options: list[str] = Field(default_factory=list)
