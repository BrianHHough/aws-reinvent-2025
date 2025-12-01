# app/slack_client.py
"""
Lightweight Slack helper for sending messages to channels or users (DMs).

Env vars expected:
  SLACK_BOT_TOKEN            -> xoxb-... from Slack "OAuth & Permissions"
  SLACK_DEFAULT_CHANNEL_ID   -> optional; fallback channel (e.g. C0123456789)
"""

import os
from typing import Optional

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_DEFAULT_CHANNEL_ID = os.getenv("SLACK_DEFAULT_CHANNEL_ID")

_client: Optional[AsyncWebClient] = None


def _get_client() -> Optional[AsyncWebClient]:
    """Lazy-init Slack AsyncWebClient. Returns None if token not set."""
    global _client
    if not SLACK_BOT_TOKEN:
        print("⚠️ SLACK_BOT_TOKEN is not set; Slack messaging disabled.")
        return None

    if _client is None:
        _client = AsyncWebClient(token=SLACK_BOT_TOKEN)

    return _client


async def send_channel_message(text: str, channel_id: Optional[str] = None) -> None:
    """
    Send a message to a Slack channel.

    If channel_id is None, uses SLACK_DEFAULT_CHANNEL_ID.
    """
    client = _get_client()
    if client is None:
        return

    target_channel = channel_id or SLACK_DEFAULT_CHANNEL_ID
    if not target_channel:
        print("⚠️ No channel_id provided and SLACK_DEFAULT_CHANNEL_ID not set.")
        return

    try:
        await client.chat_postMessage(channel=target_channel, text=text)
    except SlackApiError as e:
        # e.response["error"] has Slack's error code string
        print(f"❌ Slack API error (channel message): {e.response.get('error')}")
    except Exception as e:
        print(f"❌ Error sending Slack channel message: {e}")


async def send_dm(user_id: str, text: str) -> None:
    """
    Open a DM with a user and send them a message.

    Requires scopes:
      - im:write
      - users:read (if you ever want to look users up)
    """
    client = _get_client()
    if client is None:
        return

    try:
        # Open (or reuse) a DM channel with this user
        open_resp = await client.conversations_open(users=user_id)
        dm_channel_id = open_resp["channel"]["id"]

        await client.chat_postMessage(channel=dm_channel_id, text=text)
    except SlackApiError as e:
        print(f"❌ Slack API error (DM): {e.response.get('error')}")
    except Exception as e:
        print(f"❌ Error sending Slack DM: {e}")
