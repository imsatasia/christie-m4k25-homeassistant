"""Test the Christie M 4K25 binary sensor platform."""

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from .conftest import get_state, make_snapshot

LITELOC = "binary_sensor.christie_m_4k25_rgb_192_0_2_50_liteloc"
ALARM = "binary_sensor.christie_m_4k25_rgb_192_0_2_50_alarm"


async def test_liteloc_and_alarm_reflect_snapshot(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """LiteLOC on, no alarms -> on/off respectively."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, LITELOC).state == STATE_ON
    assert get_state(hass, ALARM).state == STATE_OFF


async def test_alarm_on_when_alarms_present(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Any alarm count above zero turns the problem binary sensor on."""
    mock_projector.snapshot.return_value = make_snapshot(alarms=2)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, ALARM).state == STATE_ON
