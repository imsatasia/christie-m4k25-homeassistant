"""Sensor platform for the Christie M 4K25 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature

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
class ChristieSensorEntityDescription(SensorEntityDescription):
    """Describes a Christie M 4K25 sensor entity."""

    value_fn: Callable[[Snapshot], object]


SENSORS: tuple[ChristieSensorEntityDescription, ...] = (
    ChristieSensorEntityDescription(
        key="status",
        translation_key="status",
        name="Status",
        value_fn=lambda snap: snap.power,
    ),
    ChristieSensorEntityDescription(
        key="input",
        translation_key="input",
        name="Input",
        value_fn=lambda snap: snap.input_name or None,
    ),
    ChristieSensorEntityDescription(
        key="hours",
        translation_key="hours",
        name="Hours",
        # The projector formats this itself, e.g. "3:14 (h:m)" -- not a
        # number, so this stays a text sensor rather than a duration one.
        value_fn=lambda snap: snap.hours or None,
    ),
    ChristieSensorEntityDescription(
        key="intake_temperature",
        translation_key="intake_temperature",
        name="Intake Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda snap: snap.intake_temp,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    data: ChristieIntegrationData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ChristieSensor(data.coordinator, description) for description in SENSORS)


class ChristieSensor(ChristieEntity, SensorEntity):
    """Representation of a Christie M 4K25 sensor."""

    entity_description: ChristieSensorEntityDescription

    def __init__(
        self,
        coordinator: ChristieCoordinator,
        entity_description: ChristieSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{self._attr_unique_id}-{entity_description.key}"

    @property
    def native_value(self) -> object:
        """Return the sensor value."""
        snap = self._snapshot
        return self.entity_description.value_fn(snap) if snap else None
