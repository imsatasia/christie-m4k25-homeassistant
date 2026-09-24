"""Number platform for the Christie M 4K25 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from christie_mseries import BRIGHTNESS_MAX_PERCENT, BRIGHTNESS_MIN_PERCENT
from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
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

# The lens motors have no published range -- getAttributes only returns a
# label for FCS/ZOM/LHO/LVO, because the real limits depend on the lens
# fitted (see py-christie-mseries's README and the Control4 driver's AGENTS.md,
# which both make the same call: send what the user asked for and let the
# projector reject anything out of range). These bounds are generous UI
# limits for the slider/box, not an authoritative range -- observed positions
# on this unit's lens stay within roughly -1200 to 1200.
_LENS_RANGE = 2000.0


@dataclass(frozen=True, kw_only=True)
class ChristieNumberEntityDescription(NumberEntityDescription):
    """Describes a Christie M 4K25 number entity."""

    value_fn: Callable[[Snapshot], float | None]
    set_value_fn: Callable[[ChristieCommands, float], Coroutine[Any, Any, None]]


NUMBERS: tuple[ChristieNumberEntityDescription, ...] = (
    ChristieNumberEntityDescription(
        key="brightness",
        translation_key="brightness",
        name="Brightness",
        native_unit_of_measurement="%",
        native_min_value=BRIGHTNESS_MIN_PERCENT,
        native_max_value=BRIGHTNESS_MAX_PERCENT,
        native_step=1,
        value_fn=lambda snap: snap.brightness,
        set_value_fn=lambda commands, value: commands.async_set_brightness(value),
    ),
    ChristieNumberEntityDescription(
        key="lens_focus",
        translation_key="lens_focus",
        name="Lens Focus",
        mode=NumberMode.BOX,
        native_min_value=-_LENS_RANGE,
        native_max_value=_LENS_RANGE,
        native_step=1,
        entity_registry_enabled_default=False,
        value_fn=lambda snap: snap.focus,
        set_value_fn=lambda commands, value: commands.async_set_lens_position("focus", int(value)),
    ),
    ChristieNumberEntityDescription(
        key="lens_zoom",
        translation_key="lens_zoom",
        name="Lens Zoom",
        mode=NumberMode.BOX,
        native_min_value=-_LENS_RANGE,
        native_max_value=_LENS_RANGE,
        native_step=1,
        entity_registry_enabled_default=False,
        value_fn=lambda snap: snap.zoom,
        set_value_fn=lambda commands, value: commands.async_set_lens_position("zoom", int(value)),
    ),
    ChristieNumberEntityDescription(
        key="lens_horizontal",
        translation_key="lens_horizontal",
        name="Lens Horizontal",
        mode=NumberMode.BOX,
        native_min_value=-_LENS_RANGE,
        native_max_value=_LENS_RANGE,
        native_step=1,
        entity_registry_enabled_default=False,
        value_fn=lambda snap: snap.lens_horizontal,
        set_value_fn=lambda commands, value: commands.async_set_lens_position(
            "horizontal", int(value)
        ),
    ),
    ChristieNumberEntityDescription(
        key="lens_vertical",
        translation_key="lens_vertical",
        name="Lens Vertical",
        mode=NumberMode.BOX,
        native_min_value=-_LENS_RANGE,
        native_max_value=_LENS_RANGE,
        native_step=1,
        entity_registry_enabled_default=False,
        value_fn=lambda snap: snap.lens_vertical,
        set_value_fn=lambda commands, value: commands.async_set_lens_position(
            "vertical", int(value)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ChristieNumber(data.coordinator, data.commands, description) for description in NUMBERS
    )


class ChristieNumber(ChristieEntity, NumberEntity):
    """Representation of a Christie M 4K25 number entity."""

    entity_description: ChristieNumberEntityDescription

    def __init__(
        self,
        coordinator: ChristieCoordinator,
        commands: ChristieCommands,
        entity_description: ChristieNumberEntityDescription,
    ) -> None:
        """Initialize number entity."""
        super().__init__(coordinator)
        self._commands = commands
        self.entity_description = entity_description
        self._attr_unique_id = f"{self._attr_unique_id}-{entity_description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        snap = self._snapshot
        return self.entity_description.value_fn(snap) if snap else None

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        try:
            await self.entity_description.set_value_fn(self._commands, value)
        except Exception as exc:
            raise HomeAssistantError(str(exc)) from exc
        await self.coordinator.async_request_refresh()
