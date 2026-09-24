"""Test the Christie M 4K25 domain services."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from custom_components.christie_m4k25.const import DOMAIN

from .conftest import make_snapshot


async def _setup(hass: HomeAssistant, mock_config_entry):
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_save_then_recall_lens_preset(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Saving a preset persists the current lens position; recalling it
    replays all four axes as absolute moves, the same synthesis the Control4
    driver does since the projector has no lens memory of its own."""
    await _setup(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "save_lens_preset", {"preset": "1"}, blocking=True)

    await hass.services.async_call(DOMAIN, "recall_lens_preset", {"preset": "1"}, blocking=True)
    await hass.async_block_till_done()

    snap = make_snapshot()
    mock_projector.set_focus.assert_called_once_with(snap.focus)
    mock_projector.set_zoom.assert_called_once_with(snap.zoom)
    mock_projector.set_lens_horizontal.assert_called_once_with(snap.lens_horizontal)
    mock_projector.set_lens_vertical.assert_called_once_with(snap.lens_vertical)


async def test_recall_unsaved_preset_raises(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """Recalling a slot that was never saved is a clear error, not a no-op."""
    await _setup(hass, mock_config_entry)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "recall_lens_preset", {"preset": "4"}, blocking=True)


async def test_recall_lens_preset_refused_in_standby(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Lens moves -- including a preset recall -- are refused in standby,
    same as the Control4 driver's LensMovable() gate."""
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(DOMAIN, "save_lens_preset", {"preset": "2"}, blocking=True)

    mock_projector.snapshot.return_value = make_snapshot(is_on=False)
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    await entry_data.coordinator.async_request_refresh()
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "recall_lens_preset", {"preset": "2"}, blocking=True)


async def test_send_raw_query(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """A query command (ending in "?") calls raw_query with code/subcode split out."""
    await _setup(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "send_raw", {"command": "LAS+POWR?"}, blocking=True)

    mock_projector.raw_query.assert_called_once_with("LAS", subcode="POWR")


async def test_send_raw_set_with_data(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """A SET command splits code(+subcode) from its data value on the first space."""
    await _setup(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "send_raw", {"command": "SHU 1"}, blocking=True)

    mock_projector.raw_set.assert_called_once_with("SHU", subcode=None, data="1")


async def test_send_raw_bare_command(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """A bare command with no data value is sent with data=None."""
    await _setup(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "send_raw", {"command": "ASU"}, blocking=True)

    mock_projector.raw_set.assert_called_once_with("ASU", subcode=None, data=None)


async def test_send_raw_rejects_command_that_breaks_wire_framing(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """py-christie-mseries's build_message() raises ValueError for a
    code/subcode/data shape that would smuggle a second "(...)" command past
    the wire framing -- this must surface as a clean ServiceValidationError,
    not an unhandled exception."""
    await _setup(hass, mock_config_entry)
    mock_projector.raw_set.side_effect = ValueError(
        "invalid data: parentheses would corrupt the framing"
    )

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "send_raw", {"command": "SHU 1) ($PWR 0"}, blocking=True
        )
