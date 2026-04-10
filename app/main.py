"""
LINE Food Ordering Bot — Margaret's Story
===========================================
Static conversation state machine that handles the full food ordering flow:
  Greeting → Category → Restaurant → Menu → Order → Payment → Delivery → Review

Endpoints:
    POST /line-webhook  — Receives LINE messages, routes through conversation FSM
    GET  /health        — Health check

Run:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Request, HTTPException

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.handlers.line_webhook_handler import handle_line_events
from app.handlers.sendbird_webhook_handler import handle_sendbird_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LINE Food Ordering Bot",
    description="Static food ordering demo with conversation state machine",
    version="0.3.0",
)

line = LineClient()
sendbird = SendbirdClient()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health")
async def health():
    return {"status": "ok", "service": "line-food-ordering-bot"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LINE WEBHOOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/line-webhook")
async def line_webhook(request: Request):
    """
    Receive LINE messages and route through the conversation state machine.

    Flow:
        User types in LINE → this endpoint
        → verify signature
        → conversation handler (FSM)
        → reply with rich messages (Flex carousels, quick replies, etc.)
    """
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # TODO: Re-enable signature verification before production deployment
    if not line.verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body)
    logger.info("[LINE] Webhook payload: %s", json.dumps(payload, ensure_ascii=False))

    await handle_line_events(line, payload.get("events", []))

    return {"status": "ok"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SENDBIRD WEBHOOK — Sendbird AI Agent → LINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/sendbird-webhook")
async def sendbird_webhook(request: Request):
    """
    Receive AI Agent responses from Sendbird, forward to LINE user.

    Flow:
        AI Agent responds in Sendbird channel
        → Sendbird fires webhook to this endpoint
        → parse message content + optional data field
        → convert to LINE message format (text / Flex Carousel / buttons / quick reply)
        → push to LINE user
    """
    payload = await request.json()
    logger.info("[SB] Webhook payload: %s", json.dumps(payload, ensure_ascii=False))

    await handle_sendbird_event(line, sendbird, payload)

    return {"status": "ok"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENTRYPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import uvicorn
    from app.config.settings import get_settings

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
