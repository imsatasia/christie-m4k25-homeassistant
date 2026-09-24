"""Test the Christie M 4K25 integration setup/unload."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.christie_m4k25.const import DOMAIN


async def test_setup_and_unload_entry(hass: HomeAssistant, mock_config_entry, mock_setup_entry):
    """A config entry sets up successfully and cleans up on unload."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert DOMAIN not in hass.data


async def test_setup_creates_expected_entities(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """Setting up an entry creates one entity per platform description."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("switch.christie_m_4k25_rgb_192_0_2_50_power")
    assert hass.states.get("switch.christie_m_4k25_rgb_192_0_2_50_shutter")
    assert hass.states.get("number.christie_m_4k25_rgb_192_0_2_50_brightness")
    assert hass.states.get("select.christie_m_4k25_rgb_192_0_2_50_test_pattern")
    assert hass.states.get("sensor.christie_m_4k25_rgb_192_0_2_50_status")
    assert hass.states.get("binary_sensor.christie_m_4k25_rgb_192_0_2_50_liteloc")
