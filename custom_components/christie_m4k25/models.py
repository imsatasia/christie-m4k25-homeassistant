"""Data models for the Christie M 4K25 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.helpers.storage import Store

    from .commands import ChristieCommands
    from .coordinator import ChristieCoordinator


@dataclass
class ChristieIntegrationData:
    """Runtime data for a config entry."""

    host: str
    port: int
    coordinator: ChristieCoordinator
    commands: ChristieCommands
    lens_preset_store: Store
