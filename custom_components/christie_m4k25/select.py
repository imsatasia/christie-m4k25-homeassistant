"""Select platform for the Christie M 4K25 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ChristieInputSelect(data.coordinator, data.commands),
            ChristieTestPatternSelect(data.coordinator, data.commands),
            *(
                ChristieThreeDSelect(data.coordinator, data.commands, description)
                for description in THREE_D_SELECTS
            ),
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


@dataclass(frozen=True, kw_only=True)
class ChristieThreeDSelectEntityDescription(SelectEntityDescription):
    """Describes one of the projector's enumerated 3D controls."""

    current_fn: Callable[[Snapshot], str]
    options_fn: Callable[[Snapshot], list[str]]
    select_fn: Callable[[ChristieCommands, str], Coroutine[Any, Any, None]]
    # The projector refuses a control its current 3D mode disables with
    # "Disabled Control", so the select is unavailable then rather than
    # offering a choice that would only raise.
    available_fn: Callable[[Snapshot], bool]


THREE_D_SELECTS: tuple[ChristieThreeDSelectEntityDescription, ...] = (
    ChristieThreeDSelectEntityDescription(
        key="three_d_mode",
        translation_key="three_d_mode",
        name="3D Mode",
        current_fn=lambda snap: snap.three_d_mode,
        options_fn=lambda snap: snap.three_d_modes,
        select_fn=lambda commands, option: commands.async_set_3d_mode(option),
        available_fn=lambda snap: snap.is_on,
    ),
    ChristieThreeDSelectEntityDescription(
        key="three_d_sync_output",
        translation_key="three_d_sync_output",
        name="3D Sync Output",
        current_fn=lambda snap: snap.three_d_sync_output,
        options_fn=lambda snap: snap.three_d_sync_outputs,
        select_fn=lambda commands, option: commands.async_set_3d_sync_output(option),
        available_fn=lambda snap: snap.is_on and snap.three_d_timing,
    ),
)


class ChristieThreeDSelect(ChristieEntity, SelectEntity):
    """A 3D select: the mode, or where the sync signal goes."""

    entity_description: ChristieThreeDSelectEntityDescription

    def __init__(
        self,
        coordinator: ChristieCoordinator,
        commands: ChristieCommands,
        entity_description: ChristieThreeDSelectEntityDescription,
    ) -> None:
        """Initialize select entity."""
        super().__init__(coordinator)
        self._commands = commands
        self.entity_description = entity_description
        self._attr_unique_id = f"{self._attr_unique_id}-{entity_description.key}"

    @property
    def current_option(self) -> str | None:
        """Return what the projector is currently set to."""
        snap = self._snapshot
        return self.entity_description.current_fn(snap) if snap else None

    @property
    def options(self) -> list[str]:
        """Return the selectable options.

        A value the library does not know (newer firmware) is listed too, so
        the select shows the current setting rather than going blank, though
        it can't be chosen.
        """
        snap = self._snapshot
        if snap is None:
            return []
        options = list(self.entity_description.options_fn(snap))
        current = self.entity_description.current_fn(snap)
        if current and current not in options:
            options.append(current)
        return options

    @property
    def available(self) -> bool:
        """Only usable while the projector is on and the 3D mode allows it."""
        snap = self._snapshot
        return super().available and snap is not None and self.entity_description.available_fn(snap)

    async def async_select_option(self, option: str) -> None:
        """Apply the chosen setting."""
        snap = self._snapshot
        if snap is None or option not in self.entity_description.options_fn(snap):
            raise HomeAssistantError(f"{option!r} is not a selectable option")
        try:
            await self.entity_description.select_fn(self._commands, option)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_request_refresh()
