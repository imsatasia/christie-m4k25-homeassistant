"""Test the Christie M 4K25 switch platform."""

from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from .conftest import get_state, make_snapshot

POWER = "switch.christie_m_4k25_rgb_192_0_2_50_power"
SHUTTER = "switch.christie_m_4k25_rgb_192_0_2_50_shutter"


async def test_switches_reflect_snapshot(hass: HomeAssistant, mock_config_entry, mock_setup_entry):
    """Switch entities are created and reflect the snapshot."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, POWER).state == STATE_ON
    assert get_state(hass, SHUTTER).state == STATE_ON


async def test_switches_reflect_off_snapshot(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Power/shutter switches go off when the snapshot says so."""
    mock_projector.snapshot.return_value = make_snapshot(is_on=False, shutter_open=False)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, POWER).state == STATE_OFF
    assert get_state(hass, SHUTTER).state == STATE_OFF


async def test_power_turn_on_calls_power_on(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Turning on the power switch calls power_on() through a connection."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: POWER}, blocking=True
    )

    mock_projector.power_on.assert_called_once()


async def test_shutter_turn_off_calls_close_shutter(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Turning off the shutter switch calls close_shutter()."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SHUTTER}, blocking=True
    )

    mock_projector.close_shutter.assert_called_once()
