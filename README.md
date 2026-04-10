# LINE Food Ordering Bot

A middleware server that bridges **LINE Messaging API** with **Sendbird AI Agent** for food ordering. Includes a fully interactive static demo with a conversation state machine.

## Architecture

```
LINE User <-> LINE Platform <-> [This Server] <-> Sendbird AI Agent
                                 /line-webhook     /sendbird-webhook
```

### Current: Static Conversation Demo

A 14-state conversation state machine that handles the complete ordering flow:

```
Greeting -> Category -> Restaurant -> Menu -> Special Request
-> Order Summary -> Payment -> Delivery Tracking -> Review
```

Features:
- **Flex Carousels** for restaurants and menu items (swipeable cards with images)
- **Quick Replies** for guided interaction (auto-dismiss after tap)
- **Flex Bubbles** for order summary (structured card with price breakdown)
- **Proactive push messages** for real-time delivery tracking simulation
- **Review flow** with star rating and highlight selection

### Future: Sendbird AI Agent Integration

The server forwards LINE messages to Sendbird AI Agent and converts AI Agent responses (via `message.data` JSON field) into rich LINE messages (carousels, buttons, quick replies).

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
```

### 3. Run

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Expose (for LINE webhooks)

```bash
ngrok http 8000 --domain=your-domain.ngrok-free.app
```

### 5. Set Webhook URLs

- **LINE Developer Console** -> Messaging API -> Webhook URL:
  `https://your-domain.ngrok-free.app/line-webhook`
- **Sendbird Dashboard** -> AI Agent -> bot_callback_url:
  `https://your-domain.ngrok-free.app/sendbird-webhook`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/line-webhook` | Receives LINE messages, routes through conversation FSM |
| `POST` | `/sendbird-webhook` | Receives Sendbird AI Agent responses, pushes to LINE |
| `GET` | `/health` | Health check |

## Project Structure

```
app/
├── main.py                          # FastAPI endpoints
├── config/settings.py               # Pydantic settings from .env
├── data/static_menu.py              # 4 categories x 3 restaurants x 3 items
├── models/
│   ├── menu.py                      # Restaurant, MenuItem
│   └── messages.py                  # Sendbird AI Agent response models
├── utils/text_matching.py           # Greeting detection, fuzzy matching
├── handlers/
│   ├── line_webhook_handler.py      # LINE event routing (dedup, verify)
│   ├── conversation_handler.py      # FSM core (14 states, per-user sessions)
│   └── sendbird_webhook_handler.py  # Sendbird -> LINE forwarding
├── builders/
│   ├── conversation_messages.py     # 20+ LINE message builders
│   ├── flex_carousel.py             # Generic Flex Carousel/Bubble builders
│   └── message_converter.py         # AI Agent data -> LINE message converter
└── services/
    ├── line_client.py               # LINE API client (reply/push/verify)
    ├── sendbird_client.py           # Sendbird API client
    └── delivery_tracker.py          # Background asyncio task for tracking
```

## Conversation Flow

The bot guides users through a complete food ordering experience:

1. **Greeting** - User says "Hello" -> category quick replies
2. **Category** - Noodles / Rice & Mains / Fast Food / Healthy
3. **Restaurant** - Flex carousel with 3 restaurants (rating, delivery time, price)
4. **Menu** - Flex carousel with menu items (image, description, price, Order button)
5. **Special Request** - Optional note (e.g., "no onions, extra spicy")
6. **Order Summary** - Flex bubble with item, delivery fee, total, address
7. **Payment** - LINE Pay / Cash / Credit Card
8. **Delivery Tracking** - Proactive push messages (preparing -> rider -> delivered)
9. **Review** - Star rating + highlight tags

Type "Hello" at any point to restart the conversation.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Static Menu Data

| Category | Restaurants |
|----------|-------------|
| Noodles | Uncle Sam's Noodle House, Mama Chen's Noodles, Old Town Beef Noodles |
| Rice & Mains | Thai Basil Kitchen, Seoul Kitchen, Hainanese Delight |
| Fast Food | Burger Lab, Pizza Express, Fried Chicken Co. |
| Healthy | Green Bowl, Poke Paradise, Juice & Co. |

Each restaurant has 3 menu items with images, descriptions, and prices.

## Tech Stack

- **Python 3.11+** / **FastAPI** / **uvicorn**
- **httpx** for async HTTP
- **Pydantic v2** for models and settings
- **LINE Messaging API** (Flex Messages, Quick Replies, Push API)
- **Sendbird Platform API** + AI Agent Messenger API

## License

MIT
