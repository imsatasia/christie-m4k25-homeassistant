"""Domain services for the Christie M 4K25 integration.

Lens presets are synthesised here the same way the Control4 driver
synthesises them: the projector has no lens memory of its own (see
py-christie-mseries's README, "No ILS / lens memory"), so SaveLensPreset
persists the four current motor positions and RecallLensPreset replays them
as absolute moves. Home Assistant's Store helper stands in for the driver's
C4:PersistSetValue/PersistGetValue.
"""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    ATTR_PRESET,
    DOMAIN,
    LENS_AXES,
    LENS_PRESET_SLOTS,
    SERVICE_RECALL_LENS_PRESET,
    SERVICE_SAVE_LENS_PRESET,
    SERVICE_SEND_RAW,
)
from .models import ChristieIntegrationData

_LOGGER = logging.getLogger(__name__)

SERVICES_DATA_KEY = f"{DOMAIN}_services_registered"


def _resolve_entry_data(hass: HomeAssistant, entry_id: str | None) -> ChristieIntegrationData:
    """Resolve which loaded config entry a service call targets."""
    entries: dict[str, ChristieIntegrationData] = hass.data.get(DOMAIN, {})
    if not entries:
        raise HomeAssistantError("No Christie M 4K25 entries are loaded")

    if entry_id:
        data = entries.get(entry_id)
        if data is None:
            raise ServiceValidationError(
                f"Unknown Christie M 4K25 entry_id: {entry_id}",
                translation_domain=DOMAIN,
                translation_key="invalid_entry_id",
                translation_placeholders={"entry_id": entry_id},
            )
        return data

    if len(entries) == 1:
        return next(iter(entries.values()))

    raise ServiceValidationError(
        "Multiple Christie M 4K25 entries loaded; provide entry_id.",
        translation_domain=DOMAIN,
        translation_key="entry_id_required",
    )


async def _async_save_lens_preset(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = call.data.get(ATTR_ENTRY_ID)
    preset = call.data[ATTR_PRESET]
    data = _resolve_entry_data(hass, entry_id)

    snap = data.coordinator.data
    if snap is None:
        raise HomeAssistantError("Lens position is not yet known; wait for a successful poll first")

    presets = await data.lens_preset_store.async_load() or {}
    presets[preset] = {
        "focus": snap.focus,
        "zoom": snap.zoom,
        "horizontal": snap.lens_horizontal,
        "vertical": snap.lens_vertical,
    }
    await data.lens_preset_store.async_save(presets)
    _LOGGER.info("Saved lens preset %s: %s", preset, presets[preset])


async def _async_recall_lens_preset(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = call.data.get(ATTR_ENTRY_ID)
    preset = call.data[ATTR_PRESET]
    data = _resolve_entry_data(hass, entry_id)

    snap = data.coordinator.data
    if snap is None or not snap.is_on:
        raise HomeAssistantError("Lens moves are rejected unless the projector is on")

    presets = await data.lens_preset_store.async_load() or {}
    position = presets.get(preset)
    if position is None:
        raise ServiceValidationError(f"Lens preset {preset} has not been saved")

    for axis in LENS_AXES:
        await data.commands.async_set_lens_position(axis, position[axis])
    await data.coordinator.async_request_refresh()


async def _async_send_raw(hass: HomeAssistant, call: ServiceCall) -> None:
    entry_id = call.data.get(ATTR_ENTRY_ID)
    command = call.data[ATTR_COMMAND].strip()
    entry_data = _resolve_entry_data(hass, entry_id)

    try:
        if command.endswith("?"):
            code, _, subcode = command.rstrip("?").partition("+")
            code, subcode = code.strip().upper(), subcode.strip().upper() or None
            reply = await entry_data.commands.async_raw_query(code, subcode)
            _LOGGER.info("Christie raw query %s -> %s", command, reply)
            return

        # A SET's code(+subcode) never contains a space, so the first space
        # separates it from an optional data value, e.g. "SHU 1" or
        # "LAS+POWR 850" -- a bare command like "ASU" has no data at all.
        head, _, tail = command.partition(" ")
        code, _, subcode = head.partition("+")
        code, subcode = code.strip().upper(), subcode.strip().upper() or None
        await entry_data.commands.async_raw_set(code, subcode, tail.strip() or None)
    except ValueError as exc:
        # py-christie-mseries's build_message() rejects a code/subcode/data
        # shape that doesn't fit the wire protocol -- including one crafted
        # to smuggle a second "(...)" command past the framing. Surface that
        # as a validation error rather than an unhandled exception.
        raise ServiceValidationError(f"Invalid raw command {command!r}: {exc}") from exc


def async_setup_services(hass: HomeAssistant) -> None:
    """Register domain services once."""
    if hass.data.get(SERVICES_DATA_KEY):
        return

    schema_preset = vol.Schema(
        {
            vol.Optional(ATTR_ENTRY_ID): cv.string,
            vol.Required(ATTR_PRESET): vol.In(LENS_PRESET_SLOTS),
        }
    )
    schema_send_raw = vol.Schema(
        {vol.Optional(ATTR_ENTRY_ID): cv.string, vol.Required(ATTR_COMMAND): cv.string}
    )

    async def handle_save_lens_preset(call: ServiceCall) -> None:
        await _async_save_lens_preset(hass, call)

    async def handle_recall_lens_preset(call: ServiceCall) -> None:
        await _async_recall_lens_preset(hass, call)

    async def handle_send_raw(call: ServiceCall) -> None:
        await _async_send_raw(hass, call)

    hass.services.async_register(
        DOMAIN, SERVICE_SAVE_LENS_PRESET, handle_save_lens_preset, schema=schema_preset
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALL_LENS_PRESET,
        handle_recall_lens_preset,
        schema=schema_preset,
    )
    hass.services.async_register(DOMAIN, SERVICE_SEND_RAW, handle_send_raw, schema=schema_send_raw)
    hass.data[SERVICES_DATA_KEY] = True


def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister domain services."""
    if not hass.data.get(SERVICES_DATA_KEY):
        return
    hass.services.async_remove(DOMAIN, SERVICE_SAVE_LENS_PRESET)
    hass.services.async_remove(DOMAIN, SERVICE_RECALL_LENS_PRESET)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_RAW)
    hass.data.pop(SERVICES_DATA_KEY, None)
