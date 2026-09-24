"""Test the Christie M 4K25 select platform."""

import pytest
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .conftest import get_state, make_snapshot

INPUT = "select.christie_m_4k25_rgb_192_0_2_50_input"
TEST_PATTERN = "select.christie_m_4k25_rgb_192_0_2_50_test_pattern"


async def test_test_pattern_reflects_snapshot(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """The select's current option and options come from the snapshot."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_PATTERN)
    assert state
    assert state.state == "Off"
    assert "Color Bars" in state.attributes["options"]


async def test_test_pattern_unavailable_in_standby(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Test patterns are rejected in standby, so the select goes unavailable."""
    mock_projector.snapshot.return_value = make_snapshot(is_on=False)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, TEST_PATTERN).state == STATE_UNAVAILABLE


async def test_select_option_calls_set_test_pattern(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Selecting an option calls set_test_pattern() with the option's name."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: TEST_PATTERN, "option": "Color Bars"},
        blocking=True,
    )

    mock_projector.set_test_pattern.assert_called_once_with("Color Bars")


async def test_input_shows_port_label(hass: HomeAssistant, mock_config_entry, mock_setup_entry):
    """The current input index is shown as its physical port, not its index."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = get_state(hass, INPUT)
    assert state.state == "HDMI 2.0 Port 1"
    assert state.attributes["options"] == ["HDMI 2.0 Port 1", "HDMI 2.0 Port 2", "HDMI 2.1 Port 3"]


async def test_input_unavailable_in_standby(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Input changes are rejected in standby, so the select goes unavailable."""
    mock_projector.snapshot.return_value = make_snapshot(is_on=False)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert get_state(hass, INPUT).state == STATE_UNAVAILABLE


async def test_input_select_sends_index(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Selecting a port label passes it to the library, which resolves the SIN index."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: INPUT, "option": "HDMI 2.1 Port 3"},
        blocking=True,
    )

    mock_projector.select_input.assert_called_once_with("HDMI 2.1 Port 3")


async def test_input_unlisted_index_falls_back_to_projector_name(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """An input the library has no label for shows the projector's own name."""
    mock_projector.snapshot.return_value = make_snapshot(
        input=12, input_name="One-Port NEW", input_label="One-Port NEW"
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = get_state(hass, INPUT)
    assert state.state == "One-Port NEW"
    assert "One-Port NEW" in state.attributes["options"]

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "select",
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: INPUT, "option": "One-Port NEW"},
            blocking=True,
        )
    mock_projector.select_input.assert_not_called()
