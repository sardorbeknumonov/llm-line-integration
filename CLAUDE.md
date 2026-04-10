# LINE Food Ordering Bot — Sendbird AI Agent Integration

## Project Overview
Middleware server that bridges **LINE Messaging API** with **Sendbird AI Agent** for food ordering. Currently running as a static demo with a conversation state machine (Margaret's Story). Future phase: connect to Sendbird AI Agent for dynamic responses.

## Tech Stack
- **Python 3.11+** / **FastAPI** / **uvicorn**
- **httpx** for async HTTP
- **Pydantic v2** for models and settings
- **LINE Messaging API** (Flex Messages, Quick Replies, Push API)
- **Sendbird Platform API** + AI Agent Messenger API (future)

## Architecture

```
LINE User ←→ LINE Platform ←→ [This Server] ←→ Sendbird AI Agent (future)
                                /line-webhook     /sb-webhook
```

### Current Mode: Static Conversation FSM
The bot handles the full ordering flow locally via a 14-state state machine:
```
Greeting → Category → Restaurant → Menu → Special Request
→ Order Summary → Payment → Delivery Tracking → Review
```

### Future Mode: Sendbird AI Agent Middleware
The server forwards LINE messages to Sendbird AI Agent and converts AI Agent responses (with `message.data` JSON) into rich LINE messages.

## Project Structure

```
app/
├── main.py                          # FastAPI endpoints (/line-webhook, /health)
├── config/settings.py               # Pydantic settings from .env
├── data/static_menu.py              # 4 categories × 3 restaurants × 3 items
├── models/
│   ├── menu.py                      # Restaurant, MenuItem
│   └── messages.py                  # Sendbird AI Agent response models
├── utils/text_matching.py           # Greeting detection, fuzzy matching
├── handlers/
│   ├── line_webhook_handler.py      # LINE event routing (dedup, signature verify)
│   ├── conversation_handler.py      # ★ FSM core (14 states, per-user sessions)
│   └── sendbird_webhook_handler.py  # Sendbird → LINE (future)
├── builders/
│   ├── conversation_messages.py     # 20+ LINE message builders (Flex, QR, text)
│   ├── flex_carousel.py             # Generic Flex Carousel/Bubble builders
│   └── message_converter.py         # AI Agent data → LINE message converter
└── services/
    ├── line_client.py               # LINE API client (reply/push/verify)
    ├── sendbird_client.py           # Sendbird API client (future)
    └── delivery_tracker.py          # Background asyncio task for proactive pushes
```

## Conventions
- All credentials via environment variables (`.env`), never hardcoded
- LINE message builders return `list[dict]` — ready for LINE API
- Button/quick reply actions use `type: "message"` (text flows back to webhook)
- Per-user state stored in-memory (`dict[str, UserSession]`)
- Delivery tracking uses `asyncio.create_task()` with timed push messages
- Tests in `tests/` — run with `pytest tests/ -v`

## Key Patterns
- **State machine**: `conversation_handler.py` maps `State` enum → handler functions
- **Message builders**: Each conversation step has a dedicated builder in `conversation_messages.py`
- **Fuzzy matching**: `text_matching.py` handles user text → expected option matching
- **Dedup**: LINE webhookEventId tracked in-memory set to prevent duplicate processing

## Running

```bash
cp .env.example .env  # fill in LINE credentials
pip install -e .
uvicorn app.main:app --reload --port 8000
```

For local development with LINE webhooks:
```bash
ngrok http 8000
# Set webhook URL in LINE Developer Console: https://xxx.ngrok.io/line-webhook
```

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Environment Variables
| Variable | Description |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API token |
| `LINE_CHANNEL_SECRET` | LINE channel secret for signature verification |
| `SENDBIRD_APP_ID` | Sendbird application ID (future) |
| `SENDBIRD_API_TOKEN` | Sendbird API token (future) |
| `BOT_USER_ID` | Sendbird AI Agent bot user ID (future) |
