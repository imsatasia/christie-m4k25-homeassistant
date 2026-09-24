"""Select platform for the Christie M 4K25 integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import ChristieEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .commands import ChristieCommands
    from .coordinator import ChristieCoordinator
    from .models import ChristieIntegrationData


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ChristieInputSelect(data.coordinator, data.commands),
            ChristieTestPatternSelect(data.coordinator, data.commands),
        ]
    )


class ChristieInputSelect(ChristieEntity, SelectEntity):
    """Representation of the Christie M 4K25 input select entity."""

    _attr_translation_key = "input"
    _attr_name = "Input"

    def __init__(self, coordinator: ChristieCoordinator, commands: ChristieCommands) -> None:
        """Initialize select entity."""
        super().__init__(coordinator)
        self._commands = commands
        self._attr_unique_id = f"{self._attr_unique_id}-input-select"

    @property
    def current_option(self) -> str | None:
        """Return the port the projector is currently on."""
        snap = self._snapshot
        return snap.input_label if snap else None

    @property
    def options(self) -> list[str]:
        """Return the list of selectable inputs.

        The library labels an input it doesn't know (a different option
        module, newer firmware) with the projector's own name for it; that is
        listed too so the select shows the current input rather than going
        blank, though it can't be chosen.
        """
        snap = self._snapshot
        if snap is None:
            return []
        options = list(snap.inputs)
        if snap.input_label not in options:
            options.append(snap.input_label)
        return options

    @property
    def available(self) -> bool:
        """Input changes are rejected by the projector while it's in
        standby, so the select is only usable while it's on."""
        snap = self._snapshot
        return super().available and snap is not None and snap.is_on

    async def async_select_option(self, option: str) -> None:
        """Switch the projector to the chosen input."""
        snap = self._snapshot
        if snap is None or option not in snap.inputs:
            raise HomeAssistantError(f"{option!r} is not a selectable input")
        try:
            await self._commands.async_select_input(option)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_request_refresh()


class ChristieTestPatternSelect(ChristieEntity, SelectEntity):
    """Representation of the Christie M 4K25 test pattern select entity."""

    _attr_translation_key = "test_pattern"
    _attr_name = "Test Pattern"

    def __init__(self, coordinator: ChristieCoordinator, commands: ChristieCommands) -> None:
        """Initialize select entity."""
        super().__init__(coordinator)
        self._commands = commands
        self._attr_unique_id = f"{self._attr_unique_id}-test-pattern-select"

    @property
    def current_option(self) -> str | None:
        """Return the current test pattern."""
        snap = self._snapshot
        return snap.test_pattern if snap else None

    @property
    def options(self) -> list[str]:
        """Return the list of available test patterns."""
        snap = self._snapshot
        return list(snap.test_patterns) if snap else []

    @property
    def available(self) -> bool:
        """Test patterns are rejected by the projector while it's in
        standby, so the select is only usable while it's on."""
        snap = self._snapshot
        return super().available and snap is not None and snap.is_on

    async def async_select_option(self, option: str) -> None:
        """Change the displayed test pattern."""
        try:
            await self._commands.async_set_test_pattern(option)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_request_refresh()
