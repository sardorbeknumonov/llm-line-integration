"""LINE Messaging API client — handles all outbound messages."""

from __future__ import annotations

import hashlib
import hmac
import base64
import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

LINE_API_BASE = "https://api.line.me/v2/bot/message"


class LineClient:
    """Thin async wrapper around the LINE Messaging API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.line_channel_access_token
        self._secret = settings.line_channel_secret
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    # ── Signature verification ──────────────────

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify that the request really came from LINE."""
        digest = hmac.new(
            self._secret.encode(), body, hashlib.sha256
        ).digest()
        expected = base64.b64encode(digest).decode()
        return hmac.compare_digest(signature, expected)

    # ── Core send methods ───────────────────────

    async def reply(self, reply_token: str, messages: list[dict]) -> dict:
        """Reply to a webhook event (free, must be within 1 min)."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}/reply",
                headers=self._headers,
                json={"replyToken": reply_token, "messages": messages[:5]},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("LINE reply sent (%d messages)", len(messages))
            return resp.json()

    async def push(self, to: str, messages: list[dict]) -> dict:
        """Push message to a user (costs quota)."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}/push",
                headers=self._headers,
                json={"to": to, "messages": messages[:5]},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("LINE push sent to %s (%d messages)", to[:8], len(messages))
            return resp.json()

    async def broadcast(self, messages: list[dict]) -> dict:
        """Broadcast to all followers."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{LINE_API_BASE}/broadcast",
                headers=self._headers,
                json={"messages": messages[:5]},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()

    # ── Convenience helpers ─────────────────────

    async def reply_text(self, reply_token: str, text: str) -> dict:
        return await self.reply(reply_token, [{"type": "text", "text": text}])

    async def reply_flex(
        self, reply_token: str, alt_text: str, contents: dict
    ) -> dict:
        return await self.reply(reply_token, [
            {"type": "flex", "altText": alt_text, "contents": contents},
        ])

    async def reply_with_header(
        self,
        reply_token: str,
        header_text: str,
        flex_alt_text: str,
        flex_contents: dict,
    ) -> dict:
        """Reply with a text header message followed by a flex message."""
        return await self.reply(reply_token, [
            {"type": "text", "text": header_text},
            {"type": "flex", "altText": flex_alt_text, "contents": flex_contents},
        ])

    async def get_user_profile(self, user_id: str) -> dict:
        """Fetch LINE user profile (display name, picture, etc.)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
