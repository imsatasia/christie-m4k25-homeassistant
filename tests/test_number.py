"""Test the Christie M 4K25 number platform."""

import pytest
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

BRIGHTNESS = "number.christie_m_4k25_rgb_192_0_2_50_brightness"


async def test_brightness_reflects_snapshot(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """Brightness number reflects the snapshot's value."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(BRIGHTNESS)
    assert state
    assert float(state.state) == 70.0


async def test_set_brightness_calls_set_brightness(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Setting brightness calls set_brightness() with the requested percent."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: BRIGHTNESS, "value": 85},
        blocking=True,
    )

    mock_projector.set_brightness.assert_called_once_with(85.0)


async def test_set_brightness_out_of_range_raises(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """A rejected value surfaces as a HomeAssistantError, not a silent failure."""
    mock_projector.set_brightness.side_effect = ValueError(
        "Brightness must be between 30.0 and 100.0"
    )

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "number",
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: BRIGHTNESS, "value": 10},
            blocking=True,
        )
