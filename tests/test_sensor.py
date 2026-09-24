"""Test the Christie M 4K25 sensor platform."""

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .conftest import get_state, make_snapshot

STATUS = "sensor.christie_m_4k25_rgb_192_0_2_50_status"
INPUT = "sensor.christie_m_4k25_rgb_192_0_2_50_input"
HOURS = "sensor.christie_m_4k25_rgb_192_0_2_50_hours"
INTAKE_TEMP = "sensor.christie_m_4k25_rgb_192_0_2_50_intake_temperature"


async def test_sensors_reflect_snapshot(hass: HomeAssistant, mock_config_entry, mock_setup_entry):
    """Sensors read straight off the snapshot's fields."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, STATUS).state == "On"
    assert get_state(hass, INPUT).state == "One-Port HDMI0"
    assert get_state(hass, HOURS).state == "3:14 (h:m)"
    assert float(get_state(hass, INTAKE_TEMP).state) == 32.0


async def test_intake_temperature_none_when_unreadable(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """intake_temp can be None -- no digits in the reading, or it timed out."""
    mock_projector.snapshot.return_value = make_snapshot(intake_temp=None)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, INTAKE_TEMP).state == STATE_UNKNOWN
