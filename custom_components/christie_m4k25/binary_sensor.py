"""Binary sensor platform for the Christie M 4K25 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import DOMAIN
from .entity import ChristieEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from christie_mseries import Snapshot
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ChristieCoordinator
    from .models import ChristieIntegrationData


@dataclass(frozen=True, kw_only=True)
class ChristieBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Christie M 4K25 binary sensor entity."""

    value_fn: Callable[[Snapshot], bool]


BINARY_SENSORS: tuple[ChristieBinarySensorEntityDescription, ...] = (
    ChristieBinarySensorEntityDescription(
        key="liteloc",
        translation_key="liteloc",
        name="LiteLOC",
        # Read-only: LAS+STAT is exposed as `set_liteloc()` in the library,
        # but this unit reports it as enabled:false (greyed out) in its own
        # menu, so it's shown here rather than offered as a switch.
        value_fn=lambda snap: snap.liteloc,
    ),
    ChristieBinarySensorEntityDescription(
        key="alarm",
        translation_key="alarm",
        name="Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda snap: snap.alarms > 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ChristieBinarySensor(data.coordinator, description) for description in BINARY_SENSORS
    )


class ChristieBinarySensor(ChristieEntity, BinarySensorEntity):
    """Representation of a Christie M 4K25 binary sensor."""

    entity_description: ChristieBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ChristieCoordinator,
        entity_description: ChristieBinarySensorEntityDescription,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{self._attr_unique_id}-{entity_description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        snap = self._snapshot
        return self.entity_description.value_fn(snap) if snap else None
