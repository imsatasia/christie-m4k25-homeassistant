"""Coordinator for the Christie M 4K25 integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from christie_mseries import ChristieM4K25
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from christie_mseries import Snapshot
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ChristieCoordinator(DataUpdateCoordinator["Snapshot"]):
    """Poll a Christie M 4K25 over its serial API (TCP).

    Each poll -- and each command -- opens a short-lived connection via
    ChristieM4K25.snapshot(), rather than holding one open across Home
    Assistant's lifecycle. The client is synchronous (plain blocking
    sockets, one request/response at a time -- see py-christie-mseries's
    AGENTS.md for why it stays that way), so every call here runs through
    hass.async_add_executor_job() rather than being rewritten as async.
    """

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port

    async def _async_update_data(self) -> Snapshot:
        """Poll everything worth polling in one shot.

        A read failure here -- including the few seconds right after a power
        command, when the projector accepts the TCP connection but answers
        nothing at all -- surfaces as an UpdateFailed and one skipped poll
        cycle, which is the "unknown, not off" behavior the old YAML package
        got by checking an explicit `available` flag. DataUpdateCoordinator
        already gives every entity that for free via `last_update_success`.
        """
        try:
            return await self.hass.async_add_executor_job(self._snapshot)
        except Exception as exc:
            raise UpdateFailed(f"Error communicating with projector: {exc}") from exc

    def _snapshot(self) -> Snapshot:
        """Blocking: connect, poll, disconnect. Runs in the executor."""
        with ChristieM4K25(self.host, port=self.port, timeout=8) as projector:
            return projector.snapshot()
