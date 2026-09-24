"""Switch platform for the Christie M 4K25 integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import ChristieEntity

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from christie_mseries import Snapshot
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .commands import ChristieCommands
    from .coordinator import ChristieCoordinator
    from .models import ChristieIntegrationData


@dataclass(frozen=True, kw_only=True)
class ChristieSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Christie M 4K25 switch entity."""

    value_fn: Callable[[Snapshot], bool]
    turn_on_fn: Callable[[ChristieCommands], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[ChristieCommands], Coroutine[Any, Any, None]]
    # Power takes ~15-20s to settle and the projector answers nothing for the
    # first few seconds of it; shutter responds immediately. Either way this
    # is only about refreshing the UI promptly -- the next scheduled poll
    # would catch up regardless.
    refresh_delay: float = 2.0


SWITCHES: tuple[ChristieSwitchEntityDescription, ...] = (
    ChristieSwitchEntityDescription(
        key="power",
        translation_key="power",
        name="Power",
        value_fn=lambda snap: snap.is_on,
        turn_on_fn=lambda commands: commands.async_power_on(),
        turn_off_fn=lambda commands: commands.async_power_off(),
        refresh_delay=20.0,
    ),
    ChristieSwitchEntityDescription(
        key="shutter",
        translation_key="shutter",
        name="Shutter",
        value_fn=lambda snap: snap.shutter_open,
        turn_on_fn=lambda commands: commands.async_open_shutter(),
        turn_off_fn=lambda commands: commands.async_close_shutter(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ChristieSwitch(data.coordinator, data.commands, description) for description in SWITCHES
    )


class ChristieSwitch(ChristieEntity, SwitchEntity):
    """Representation of a Christie M 4K25 switch."""

    entity_description: ChristieSwitchEntityDescription

    def __init__(
        self,
        coordinator: ChristieCoordinator,
        commands: ChristieCommands,
        entity_description: ChristieSwitchEntityDescription,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._commands = commands
        self.entity_description = entity_description
        self._attr_unique_id = f"{self._attr_unique_id}-{entity_description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        snap = self._snapshot
        return self.entity_description.value_fn(snap) if snap else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.entity_description.turn_on_fn(self._commands)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        self._async_schedule_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.entity_description.turn_off_fn(self._commands)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        self._async_schedule_refresh()

    def _async_schedule_refresh(self) -> None:
        """Refresh the coordinator shortly after a command, without blocking
        the service call on it."""

        async def _refresh() -> None:
            await asyncio.sleep(self.entity_description.refresh_delay)
            await self.coordinator.async_request_refresh()

        self.hass.async_create_task(_refresh())
