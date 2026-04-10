"""Hardcoded restaurant and menu data for the food ordering demo."""

from __future__ import annotations

from app.models.menu import Restaurant, MenuItem

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CATEGORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CATEGORIES: list[dict] = [
    {"label": "\U0001f35c Noodles", "key": "noodles"},
    {"label": "\U0001f371 Rice & Mains", "key": "rice"},
    {"label": "\U0001f355 Fast Food", "key": "fastfood"},
    {"label": "\U0001f957 Healthy", "key": "healthy"},
]

CATEGORY_KEYS = [c["key"] for c in CATEGORIES]
CATEGORY_LABELS = [c["label"] for c in CATEGORIES]

# Map for resolving label → key
_LABEL_TO_KEY = {c["label"]: c["key"] for c in CATEGORIES}
_KEY_TO_LABEL = {c["key"]: c["label"] for c in CATEGORIES}


def resolve_category_key(text: str) -> str | None:
    """Resolve user text to a category key. Accepts label or key."""
    t = text.strip()
    if t in _LABEL_TO_KEY:
        return _LABEL_TO_KEY[t]
    if t.lower() in CATEGORY_KEYS:
        return t.lower()
    # Partial match
    tl = t.lower()
    for cat in CATEGORIES:
        if tl in cat["key"] or tl in cat["label"].lower():
            return cat["key"]
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RESTAURANTS BY CATEGORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESTAURANTS: dict[str, list[Restaurant]] = {
    # ── Noodles ──
    "noodles": [
        Restaurant(
            id="noodle-1",
            name="Uncle Sam's Noodle House",
            image_url="https://picsum.photos/seed/noodle1/800/520",
            rating=4.8,
            delivery_time_min=20,
            price_from=6.00,
            menu=[
                MenuItem(id="n1-1", name="Classic Pork Noodle Soup (Regular)", price=6.00,
                         image_url="https://picsum.photos/seed/porknoodle/800/520",
                         description="Slow-cooked pork broth with handmade noodles"),
                MenuItem(id="n1-2", name="Classic Pork Noodle Soup (Large)", price=8.00,
                         image_url="https://picsum.photos/seed/porknoodlelg/800/520",
                         description="Large bowl with extra noodles and pork"),
                MenuItem(id="n1-3", name="Spicy Beef Noodles", price=8.50,
                         image_url="https://picsum.photos/seed/beefnoodle/800/520",
                         description="Rich beef broth with chili oil and tender beef slices"),
            ],
        ),
        Restaurant(
            id="noodle-2",
            name="Mama Chen's Noodles",
            image_url="https://picsum.photos/seed/noodle2/800/520",
            rating=4.6,
            delivery_time_min=35,
            price_from=5.50,
            menu=[
                MenuItem(id="n2-1", name="Wonton Noodle Soup", price=5.50,
                         image_url="https://picsum.photos/seed/wonton/800/520",
                         description="Shrimp wontons in clear broth with egg noodles"),
                MenuItem(id="n2-2", name="Dan Dan Noodles", price=7.00,
                         image_url="https://picsum.photos/seed/dandan/800/520",
                         description="Spicy sesame sauce with minced pork"),
                MenuItem(id="n2-3", name="Chicken Noodle Soup", price=6.50,
                         image_url="https://picsum.photos/seed/chickennoodle/800/520",
                         description="Comfort classic with herbs and vegetables"),
            ],
        ),
        Restaurant(
            id="noodle-3",
            name="Old Town Beef Noodles",
            image_url="https://picsum.photos/seed/noodle3/800/520",
            rating=4.7,
            delivery_time_min=25,
            price_from=7.00,
            menu=[
                MenuItem(id="n3-1", name="Braised Beef Noodles", price=9.00,
                         image_url="https://picsum.photos/seed/braisedbeef/800/520",
                         description="8-hour braised beef in aromatic broth"),
                MenuItem(id="n3-2", name="Tomato Beef Noodles", price=8.50,
                         image_url="https://picsum.photos/seed/tomatobeef/800/520",
                         description="Tangy tomato broth with tender beef chunks"),
                MenuItem(id="n3-3", name="Dry Tossed Noodles", price=7.00,
                         image_url="https://picsum.photos/seed/drynoodle/800/520",
                         description="Chewy noodles with sesame and soy glaze"),
            ],
        ),
    ],

    # ── Rice & Mains ──
    "rice": [
        Restaurant(
            id="rice-1",
            name="Thai Basil Kitchen",
            image_url="https://picsum.photos/seed/thai1/800/520",
            rating=4.7,
            delivery_time_min=25,
            price_from=7.50,
            menu=[
                MenuItem(id="r1-1", name="Pad Kra Pao (Basil Chicken Rice)", price=7.50,
                         image_url="https://picsum.photos/seed/krapao/800/520",
                         description="Stir-fried chicken with holy basil and fried egg"),
                MenuItem(id="r1-2", name="Green Curry with Rice", price=9.00,
                         image_url="https://picsum.photos/seed/greencurry/800/520",
                         description="Creamy coconut green curry with jasmine rice"),
                MenuItem(id="r1-3", name="Mango Sticky Rice", price=5.00,
                         image_url="https://picsum.photos/seed/mangosticky/800/520",
                         description="Sweet sticky rice with fresh mango"),
            ],
        ),
        Restaurant(
            id="rice-2",
            name="Seoul Kitchen",
            image_url="https://picsum.photos/seed/korean1/800/520",
            rating=4.5,
            delivery_time_min=30,
            price_from=8.00,
            menu=[
                MenuItem(id="r2-1", name="Bibimbap", price=9.50,
                         image_url="https://picsum.photos/seed/bibimbap/800/520",
                         description="Mixed rice bowl with vegetables, beef, and gochujang"),
                MenuItem(id="r2-2", name="Kimchi Fried Rice", price=8.00,
                         image_url="https://picsum.photos/seed/kimchirice/800/520",
                         description="Spicy kimchi fried rice with pork and egg"),
                MenuItem(id="r2-3", name="Bulgogi Rice Bowl", price=10.00,
                         image_url="https://picsum.photos/seed/bulgogi/800/520",
                         description="Marinated beef with pickled vegetables"),
            ],
        ),
        Restaurant(
            id="rice-3",
            name="Hainanese Delight",
            image_url="https://picsum.photos/seed/hainanese/800/520",
            rating=4.8,
            delivery_time_min=20,
            price_from=6.50,
            menu=[
                MenuItem(id="r3-1", name="Hainanese Chicken Rice", price=6.50,
                         image_url="https://picsum.photos/seed/chickenrice/800/520",
                         description="Poached chicken with fragrant rice and 3 sauces"),
                MenuItem(id="r3-2", name="Roasted Chicken Rice", price=7.00,
                         image_url="https://picsum.photos/seed/roastchicken/800/520",
                         description="Crispy-skin roasted chicken on oiled rice"),
                MenuItem(id="r3-3", name="Chicken Chop Rice", price=8.50,
                         image_url="https://picsum.photos/seed/chickenchop/800/520",
                         description="Golden fried chicken cutlet with gravy"),
            ],
        ),
    ],

    # ── Fast Food ──
    "fastfood": [
        Restaurant(
            id="fast-1",
            name="Burger Lab",
            image_url="https://picsum.photos/seed/burger1/800/520",
            rating=4.6,
            delivery_time_min=15,
            price_from=6.00,
            menu=[
                MenuItem(id="f1-1", name="Classic Smash Burger", price=6.00,
                         image_url="https://picsum.photos/seed/smashburger/800/520",
                         description="Double patty with American cheese and secret sauce"),
                MenuItem(id="f1-2", name="BBQ Bacon Burger", price=8.50,
                         image_url="https://picsum.photos/seed/bbqburger/800/520",
                         description="Smoky BBQ sauce, crispy bacon, cheddar"),
                MenuItem(id="f1-3", name="Chicken Burger", price=7.00,
                         image_url="https://picsum.photos/seed/chickenburger/800/520",
                         description="Crispy fried chicken fillet with mayo"),
            ],
        ),
        Restaurant(
            id="fast-2",
            name="Pizza Express",
            image_url="https://picsum.photos/seed/pizza1/800/520",
            rating=4.4,
            delivery_time_min=25,
            price_from=8.00,
            menu=[
                MenuItem(id="f2-1", name="Margherita Pizza", price=8.00,
                         image_url="https://picsum.photos/seed/margherita2/800/520",
                         description="Fresh mozzarella, tomato sauce, basil"),
                MenuItem(id="f2-2", name="Pepperoni Pizza", price=10.00,
                         image_url="https://picsum.photos/seed/pepperoni/800/520",
                         description="Loaded with spicy pepperoni and cheese"),
                MenuItem(id="f2-3", name="Hawaiian Pizza", price=9.50,
                         image_url="https://picsum.photos/seed/hawaiian/800/520",
                         description="Ham and pineapple on mozzarella"),
            ],
        ),
        Restaurant(
            id="fast-3",
            name="Fried Chicken Co.",
            image_url="https://picsum.photos/seed/friedchicken/800/520",
            rating=4.5,
            delivery_time_min=20,
            price_from=5.50,
            menu=[
                MenuItem(id="f3-1", name="3pc Fried Chicken", price=5.50,
                         image_url="https://picsum.photos/seed/3pcchicken/800/520",
                         description="Golden crispy fried chicken pieces"),
                MenuItem(id="f3-2", name="Spicy Wings (6pc)", price=6.50,
                         image_url="https://picsum.photos/seed/spicywings/800/520",
                         description="Hot & spicy wings with dipping sauce"),
                MenuItem(id="f3-3", name="Chicken Tenders Meal", price=7.50,
                         image_url="https://picsum.photos/seed/tenders/800/520",
                         description="Crispy tenders with fries and coleslaw"),
            ],
        ),
    ],

    # ── Healthy ──
    "healthy": [
        Restaurant(
            id="health-1",
            name="Green Bowl",
            image_url="https://picsum.photos/seed/greenbowl/800/520",
            rating=4.7,
            delivery_time_min=20,
            price_from=8.00,
            menu=[
                MenuItem(id="h1-1", name="Quinoa Power Bowl", price=9.50,
                         image_url="https://picsum.photos/seed/quinoa/800/520",
                         description="Quinoa, avocado, roasted veggies, tahini"),
                MenuItem(id="h1-2", name="Grilled Chicken Salad", price=8.00,
                         image_url="https://picsum.photos/seed/chickensalad/800/520",
                         description="Mixed greens with grilled chicken and vinaigrette"),
                MenuItem(id="h1-3", name="Acai Smoothie Bowl", price=7.50,
                         image_url="https://picsum.photos/seed/acaibowl/800/520",
                         description="Acai blend topped with granola and fresh fruit"),
            ],
        ),
        Restaurant(
            id="health-2",
            name="Poke Paradise",
            image_url="https://picsum.photos/seed/poke1/800/520",
            rating=4.6,
            delivery_time_min=25,
            price_from=9.00,
            menu=[
                MenuItem(id="h2-1", name="Salmon Poke Bowl", price=11.00,
                         image_url="https://picsum.photos/seed/salmonpoke/800/520",
                         description="Fresh salmon, edamame, avocado, sushi rice"),
                MenuItem(id="h2-2", name="Tuna Poke Bowl", price=10.50,
                         image_url="https://picsum.photos/seed/tunapoke/800/520",
                         description="Ahi tuna with mango salsa and sesame"),
                MenuItem(id="h2-3", name="Tofu Poke Bowl", price=9.00,
                         image_url="https://picsum.photos/seed/tofupoke/800/520",
                         description="Crispy tofu, cucumber, pickled ginger"),
            ],
        ),
        Restaurant(
            id="health-3",
            name="Juice & Co.",
            image_url="https://picsum.photos/seed/juice1/800/520",
            rating=4.4,
            delivery_time_min=15,
            price_from=5.00,
            menu=[
                MenuItem(id="h3-1", name="Green Detox Smoothie", price=6.00,
                         image_url="https://picsum.photos/seed/greensmooth/800/520",
                         description="Kale, spinach, apple, ginger, lemon"),
                MenuItem(id="h3-2", name="Protein Shake", price=7.00,
                         image_url="https://picsum.photos/seed/proteinshake/800/520",
                         description="Banana, peanut butter, whey protein, oat milk"),
                MenuItem(id="h3-3", name="Avocado Toast", price=5.00,
                         image_url="https://picsum.photos/seed/avotoast/800/520",
                         description="Sourdough with smashed avocado and poached egg"),
            ],
        ),
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOOKUP HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_restaurants(category_key: str) -> list[Restaurant]:
    return RESTAURANTS.get(category_key, [])


def find_restaurant(restaurant_name: str, category_key: str | None = None) -> Restaurant | None:
    """Find a restaurant by name (case-insensitive partial match)."""
    name_lower = restaurant_name.strip().lower()
    categories = [category_key] if category_key else RESTAURANTS.keys()
    for cat in categories:
        for r in RESTAURANTS.get(cat, []):
            if name_lower == r.name.lower() or name_lower in r.name.lower():
                return r
    return None


def find_menu_item(item_text: str, restaurant: Restaurant) -> MenuItem | None:
    """Find a menu item by name or price label (case-insensitive)."""
    text_lower = item_text.strip().lower()
    for item in restaurant.menu:
        if text_lower == item.name.lower():
            return item
        if text_lower in item.name.lower():
            return item
        # Match price labels like "Regular $6" or "Large $8"
        price_label = f"${item.price:.0f}" if item.price == int(item.price) else f"${item.price:.2f}"
        if price_label in text_lower or item.name.lower() in text_lower:
            return item
    return None
