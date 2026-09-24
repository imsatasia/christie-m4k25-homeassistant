"""The Christie M 4K25 integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .commands import ChristieCommands
from .const import CONF_PORT, DEFAULT_PORT, DOMAIN
from .coordinator import ChristieCoordinator
from .models import ChristieIntegrationData
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LENS_PRESET_STORE_VERSION = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for Christie M 4K25."""
    host = entry.data[CONF_HOST].strip()
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    coordinator = ChristieCoordinator(hass, host, port)
    commands = ChristieCommands(hass, host, port)
    lens_preset_store: Store = Store(
        hass, _LENS_PRESET_STORE_VERSION, f"{DOMAIN}_{entry.entry_id}_lens_presets"
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ChristieIntegrationData(
        host=host,
        port=port,
        coordinator=coordinator,
        commands=commands,
        lens_preset_store=lens_preset_store,
    )
    async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Christie M 4K25 config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            async_unload_services(hass)
            hass.data.pop(DOMAIN, None)

    return unload_ok
