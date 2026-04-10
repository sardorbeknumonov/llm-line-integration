"""Data models for restaurants and menu items."""

from __future__ import annotations

from pydantic import BaseModel


class MenuItem(BaseModel):
    id: str
    name: str
    price: float
    image_url: str = ""
    description: str = ""


class Restaurant(BaseModel):
    id: str
    name: str
    image_url: str = ""
    rating: float = 0.0
    delivery_time_min: int = 30
    price_from: float = 0.0
    menu: list[MenuItem] = []
