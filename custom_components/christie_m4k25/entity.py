"""Base entity for the Christie M 4K25 integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, NAME
from .coordinator import ChristieCoordinator

if TYPE_CHECKING:
    from christie_mseries import Snapshot


class ChristieEntity(CoordinatorEntity[ChristieCoordinator]):
    """Base entity backed by the Christie coordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: ChristieCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        device_id = coordinator.host
        self._attr_unique_id = device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"{NAME} ({coordinator.host})",
            model=MODEL,
            manufacturer=MANUFACTURER,
            configuration_url=f"http://{coordinator.host}",
        )

    @property
    def _snapshot(self) -> Snapshot | None:
        """Return the latest coordinator-backed snapshot, if any."""
        return self.coordinator.data
