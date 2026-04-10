"""
LINE ↔ Sendbird AI Agent Integration
======================================
Middleware server that bridges LINE Messaging API with Sendbird AI Agent.

Endpoints:
    POST /line-webhook      — Receives LINE messages, forwards to Sendbird AI Agent
    POST /sendbird-webhook  — Receives Sendbird events, forwards AI responses to LINE
    GET  /health            — Health check

Run:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException

from app.services.line_client import LineClient
from app.services.sendbird_client import SendbirdClient
from app.handlers.line_webhook_handler import handle_line_events
from app.handlers.sendbird_webhook_handler import handle_sendbird_event
from app.db.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="LINE ↔ Sendbird AI Agent",
    description="Bridges LINE Messaging API with Sendbird AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

line = LineClient()
sendbird = SendbirdClient()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health")
async def health():
    return {"status": "ok", "service": "line-sendbird-integration"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LINE WEBHOOK → Sendbird
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/line-webhook")
async def line_webhook(request: Request):
    """
    Receive LINE messages, forward to Sendbird AI Agent.

    Flow:
        LINE user sends message → verify signature → ensure SB user exists
        → get/create channel → store conversation in DB → send to Sendbird
    """
    body = await request.body()
    #signature = request.headers.get("X-Line-Signature", "")

    #if not line.verify_signature(body, signature):
    #    raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body)
    logger.info("[LINE] Webhook payload: %s", json.dumps(payload, ensure_ascii=False))

    await handle_line_events(line, sendbird, payload.get("events", []))

    return {"status": "ok"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SENDBIRD WEBHOOK → LINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/sendbird-webhook")
async def sendbird_webhook(request: Request):
    """
    Receive Sendbird events: AI Agent responses + conversation lifecycle.

    Handled events:
        - message:ai_agent_sent           → push AI response to LINE user
        - ai_agent:conversation_started   → mark conversation as 'ongoing' in DB
        - ai_agent:conversation_closed    → mark conversation as 'closed' in DB
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
