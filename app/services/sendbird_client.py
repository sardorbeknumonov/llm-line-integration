"""Sendbird Platform API client — user management, channels, and messaging."""

from __future__ import annotations

import json
import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class SendbirdClient:
    """Async wrapper around Sendbird Platform API + AI Agent Messenger API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._app_id = settings.sendbird_app_id
        self._bot_user_id = settings.bot_user_id
        self._base_url = settings.sendbird_api_url
        self._headers = {
            "Content-Type": "application/json",
            "Api-Token": settings.sendbird_api_token,
        }
        # In-memory cache: sb_user_id -> channel_url
        self._user_channels: dict[str, str] = {}
        logger.info("[SB] Client initialized: base_url=%s bot=%s", self._base_url, self._bot_user_id)

    # ── User management ─────────────────────────

    async def create_user(self, user_id: str, nickname: str = "") -> bool:
        """Create a Sendbird user (idempotent — ignores 'already exists' error)."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/users",
                headers=self._headers,
                json={
                    "user_id": user_id,
                    "nickname": nickname or user_id,
                    "profile_url": "",
                    "issue_access_token": True,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info("[SB] Created user %s", user_id)
                return True
            elif resp.status_code == 400:
                body = resp.json()
                if body.get("code") == 400202:
                    logger.debug("[SB] User %s already exists", user_id)
                    return True
                logger.error("[SB] Create user failed: %s %s", resp.status_code, resp.text)
                return False
            else:
                logger.error("[SB] Create user failed: %s %s", resp.status_code, resp.text)
                return False

    # ── Channel management ──────────────────────

    async def get_or_create_channel(self, sb_user_id: str) -> str | None:
        """
        Get or create a messenger channel via the AI Agent Messenger API.

        Uses POST /v3/ai_agent/ai_agents/{bot_id}/messenger
        Returns the channel_url or None on failure.
        """
        # Check cache first
        if sb_user_id in self._user_channels:
            return self._user_channels[sb_user_id]

        # Ensure user exists
        await self.create_user(sb_user_id)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/ai_agent/ai_agents/{self._bot_user_id}/messenger",
                headers=self._headers,
                json={
                    "user_id": sb_user_id,
                    "context": {"source": "LINE"},
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                channel_url = data["active_channel"]["channel_url"]
                self._user_channels[sb_user_id] = channel_url
                logger.info("[SB] Channel ready: %s for user %s", channel_url, sb_user_id)
                return channel_url
            else:
                logger.error(
                    "[SB] Messenger API failed: %s %s", resp.status_code, resp.text
                )
                return None

    # ── Message retrieval ──────────────────────

    async def get_message(
        self, channel_url: str, message_id: int
    ) -> dict | None:
        """
        Fetch a single message with extended_message_payload.

        Returns the full message dict including suggested_replies,
        agent_message_templates, manual info, etc.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/group_channels/{channel_url}/messages/{message_id}",
                headers=self._headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(
                    "[SB] Fetched message %d from %s — payload:\n%s",
                    message_id,
                    channel_url,
                    json.dumps(data, indent=2, ensure_ascii=False),
                )
                return data
            else:
                logger.error(
                    "[SB] Get message failed: %s %s", resp.status_code, resp.text
                )
            return None

    # ── Messaging ───────────────────────────────

    async def send_message(
        self, channel_url: str, user_id: str, message: str
    ) -> bool:
        """Send a text message to a Sendbird group channel."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/group_channels/{channel_url}/messages",
                headers=self._headers,
                json={
                    "message_type": "MESG",
                    "user_id": user_id,
                    "message": message,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info("[SB] Message sent to %s by %s", channel_url, user_id)
                return True
            else:
                logger.error(
                    "[SB] Send message failed: %s %s", resp.status_code, resp.text
                )
                return False
