"""Async client for the Pulselive MotoGP API.

Data is sourced from the public Pulselive REST API used by motogp.com.
This is an unofficial integration, not affiliated with Dorna Sports.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    LIVE_SOURCE_OFFICIAL,
    LIVE_SOURCE_PULSELIVE,
    OFFICIAL_LIVE_TIMING_URL,
    PULSELIVE_BASE_URL,
    PULSELIVE_CATEGORIES_URL,
    PULSELIVE_EVENTS_URL,
    PULSELIVE_LIVE_TIMING_URL,
    PULSELIVE_SEASONS_URL,
    PULSELIVE_SESSION_CLASSIFICATION_URL,
    PULSELIVE_SESSIONS_URL,
    PULSELIVE_STANDINGS_URL,
    PULSELIVE_TEAM_STANDINGS_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class MotogpApiError(Exception):
    """Raised when the MotoGP API request fails."""


class MotogpApiClient:
    """Client for the Pulselive MotoGP API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def _request(self, url: str) -> dict[str, Any] | list[Any]:
        """Perform a GET request and return parsed JSON."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        }
        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    raise MotogpApiError(
                        f"Request to {url} failed with status {resp.status}"
                    )
                return await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise MotogpApiError(f"Request to {url} timed out") from err
        except aiohttp.ClientError as err:
            raise MotogpApiError(f"Request to {url} failed: {err}") from err

    async def async_get_seasons(self) -> list[dict[str, Any]]:
        """Return the list of seasons (current first)."""
        data = await self._request(PULSELIVE_SEASONS_URL)
        if not isinstance(data, list):
            raise MotogpApiError("Unexpected response shape from seasons endpoint")
        return data

    async def async_get_categories(self, season_uuid: str) -> list[dict[str, Any]]:
        """Return the categories for a season."""
        data = await self._request(f"{PULSELIVE_CATEGORIES_URL}?seasonUuid={season_uuid}")
        if not isinstance(data, list):
            raise MotogpApiError("Unexpected response shape from categories endpoint")
        return data

    async def async_get_events(self, season_uuid: str) -> list[dict[str, Any]]:
        """Return all events (race weekends) for a season."""
        data = await self._request(f"{PULSELIVE_EVENTS_URL}?seasonUuid={season_uuid}")
        if not isinstance(data, list):
            raise MotogpApiError("Unexpected response shape from events endpoint")
        return data

    async def async_get_sessions(
        self, event_uuid: str, category_uuid: str
    ) -> list[dict[str, Any]]:
        """Return the sessions of an event for a category."""
        url = f"{PULSELIVE_SESSIONS_URL}?eventUuid={event_uuid}&categoryUuid={category_uuid}"
        data = await self._request(url)
        if not isinstance(data, list):
            raise MotogpApiError("Unexpected response shape from sessions endpoint")
        return data

    async def async_get_classification(self, session_uuid: str) -> dict[str, Any]:
        """Return the classification of a session."""
        url = PULSELIVE_SESSION_CLASSIFICATION_URL.format(uuid=session_uuid)
        data = await self._request(url)
        if not isinstance(data, dict):
            raise MotogpApiError("Unexpected response shape from classification endpoint")
        return data

    async def async_get_standings(
        self, season_uuid: str, category_uuid: str, *, team: bool = False
    ) -> dict[str, Any]:
        """Return rider (or team) championship standings."""
        if team:
            url = PULSELIVE_TEAM_STANDINGS_URL.format(
                season_uuid=season_uuid, category_uuid=category_uuid
            )
        else:
            url = PULSELIVE_STANDINGS_URL.format(
                season_uuid=season_uuid, category_uuid=category_uuid
            )
        data = await self._request(url)
        if not isinstance(data, dict):
            raise MotogpApiError("Unexpected response shape from standings endpoint")
        return data

    async def async_get_live_timing(self, source: str) -> dict[str, Any]:
        """Return the live timing payload from the selected source."""
        if source == LIVE_SOURCE_OFFICIAL:
            url = OFFICIAL_LIVE_TIMING_URL
        else:
            url = PULSELIVE_LIVE_TIMING_URL
        data = await self._request(url)
        if not isinstance(data, dict):
            raise MotogpApiError("Unexpected response shape from live timing endpoint")
        return data

    @staticmethod
    def fallback_source(source: str) -> str:
        """Return the fallback live source for the given one."""
        if source == LIVE_SOURCE_OFFICIAL:
            return LIVE_SOURCE_PULSELIVE
        return LIVE_SOURCE_PULSELIVE
