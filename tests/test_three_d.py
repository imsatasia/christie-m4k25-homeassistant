"""Test the 3D entities: mode and sync-output selects, sync-delay and
dark-interval numbers, invert-eyes and test-pattern switches, and the two
read-only 3D sensors.

Which of them are available follows what the projector itself enforces, read
off the hardware: with the projector on, the timing controls (sync output,
sync delay, dark interval) need a packed 3D mode (Side-by-Side, Top-and-Bottom,
Frame Packing) and the invert switch needs the opposite; the mode select and
the test pattern work in every mode. The whole set is writable only while the
projector is on.
"""

import pytest
from christie_mseries import ChristieError
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .conftest import get_state, make_snapshot

PREFIX = "christie_m_4k25_rgb_192_0_2_50"
MODE = f"select.{PREFIX}_3d_mode"
SYNC_OUTPUT = f"select.{PREFIX}_3d_sync_output"
SYNC_DELAY = f"number.{PREFIX}_3d_sync_delay"
DARK_INTERVAL = f"number.{PREFIX}_3d_dark_interval"
INVERT = f"switch.{PREFIX}_3d_invert_eyes"
TEST_PATTERN = f"switch.{PREFIX}_3d_test_pattern"
SYNC = f"sensor.{PREFIX}_3d_sync"
DARKTIME = f"sensor.{PREFIX}_3d_darktime"

PACKED = {"three_d_mode": "Side-by-Side 3D", "three_d_timing": True}
TIMING_ENTITIES = (SYNC_OUTPUT, SYNC_DELAY, DARK_INTERVAL)


async def _setup(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


# --- state ------------------------------------------------------------------


async def test_entities_reflect_the_snapshot(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(
        **PACKED,
        three_d_sync_output="To Next Input",
        three_d_emitter_delay=-120,
        three_d_dark_interval=2500,
        three_d_test_pattern=True,
        three_d_sync="Valid HDMI 3D Sync",
        three_d_darktime="Achieved",
    )
    await _setup(hass, mock_config_entry)

    assert get_state(hass, MODE).state == "Side-by-Side 3D"
    assert "Frame Packing 3D" in get_state(hass, MODE).attributes["options"]
    assert get_state(hass, SYNC_OUTPUT).state == "To Next Input"
    assert get_state(hass, SYNC_OUTPUT).attributes["options"] == ["To Emitter", "To Next Input"]
    assert float(get_state(hass, SYNC_DELAY).state) == -120
    assert float(get_state(hass, DARK_INTERVAL).state) == 2500
    assert get_state(hass, TEST_PATTERN).state == STATE_ON
    assert get_state(hass, SYNC).state == "Valid HDMI 3D Sync"
    assert get_state(hass, DARKTIME).state == "Achieved"


async def test_number_ranges_are_the_projectors_published_ones(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)

    delay = get_state(hass, SYNC_DELAY).attributes
    assert (delay["min"], delay["max"]) == (-1000, 1000)
    dark = get_state(hass, DARK_INTERVAL).attributes
    assert (dark["min"], dark["max"]) == (250, 3000)
    # The projector publishes no unit for either, so none is claimed.
    assert "unit_of_measurement" not in delay
    assert "unit_of_measurement" not in dark


# --- availability -----------------------------------------------------------


async def test_idle_projector_with_3d_off(hass: HomeAssistant, mock_config_entry, mock_setup_entry):
    """3D Off: mode and test pattern and invert work; the timing controls do not."""
    await _setup(hass, mock_config_entry)

    assert get_state(hass, MODE).state == "Off"
    assert get_state(hass, INVERT).state == STATE_OFF
    assert get_state(hass, TEST_PATTERN).state == STATE_OFF
    for entity_id in TIMING_ENTITIES:
        assert get_state(hass, entity_id).state == STATE_UNAVAILABLE, entity_id


async def test_packed_mode_enables_timing_and_disables_invert(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)

    for entity_id in (MODE, TEST_PATTERN, *TIMING_ENTITIES):
        assert get_state(hass, entity_id).state != STATE_UNAVAILABLE, entity_id
    assert get_state(hass, INVERT).state == STATE_UNAVAILABLE


@pytest.mark.parametrize("mode", ["Off", "Auto Detect", "Multi-Flash 3D"])
async def test_non_packed_modes_disable_timing_and_enable_invert(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector, mode
):
    mock_projector.snapshot.return_value = make_snapshot(three_d_mode=mode, three_d_timing=False)
    await _setup(hass, mock_config_entry)

    assert get_state(hass, INVERT).state != STATE_UNAVAILABLE
    for entity_id in TIMING_ENTITIES:
        assert get_state(hass, entity_id).state == STATE_UNAVAILABLE, entity_id


async def test_writable_3d_entities_are_unavailable_in_standby(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(is_on=False, **PACKED)
    await _setup(hass, mock_config_entry)

    for entity_id in (MODE, INVERT, TEST_PATTERN, *TIMING_ENTITIES):
        assert get_state(hass, entity_id).state == STATE_UNAVAILABLE, entity_id


async def test_3d_sensors_still_read_in_standby(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(
        is_on=False, three_d_sync="N/A", three_d_darktime="N/A"
    )
    await _setup(hass, mock_config_entry)

    assert get_state(hass, SYNC).state == "N/A"
    assert get_state(hass, DARKTIME).state == "N/A"


async def test_unreported_3d_status_is_unknown_not_empty(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(three_d_sync="", three_d_darktime="")
    await _setup(hass, mock_config_entry)

    assert get_state(hass, SYNC).state == "unknown"
    assert get_state(hass, DARKTIME).state == "unknown"


async def test_a_mode_the_library_does_not_know_is_still_shown(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(three_d_mode="Dual Projector 3D")
    await _setup(hass, mock_config_entry)

    state = get_state(hass, MODE)
    assert state.state == "Dual Projector 3D"
    assert "Dual Projector 3D" in state.attributes["options"]


# --- commands ---------------------------------------------------------------


async def test_choosing_a_3d_mode_sends_its_name(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: MODE, "option": "Frame Packing 3D"},
        blocking=True,
    )
    mock_projector.set_3d_mode.assert_called_once_with("Frame Packing 3D")


async def test_choosing_a_sync_output_sends_its_name(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: SYNC_OUTPUT, "option": "To Next Input"},
        blocking=True,
    )
    mock_projector.set_3d_sync_output.assert_called_once_with("To Next Input")


async def test_an_option_the_projector_does_not_offer_is_refused(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    await _setup(hass, mock_config_entry)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "select",
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: MODE, "option": "Native 3D"},
            blocking=True,
        )
    mock_projector.set_3d_mode.assert_not_called()


async def test_a_refused_select_surfaces_as_home_assistant_error(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.set_3d_mode.side_effect = ChristieError(105, "TDM: Disabled Control")
    await _setup(hass, mock_config_entry)
    with pytest.raises(HomeAssistantError, match="Disabled Control"):
        await hass.services.async_call(
            "select",
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: MODE, "option": "Auto Detect"},
            blocking=True,
        )


async def test_setting_the_sync_delay(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "number", SERVICE_SET_VALUE, {ATTR_ENTITY_ID: SYNC_DELAY, "value": -250}, blocking=True
    )
    mock_projector.set_3d_emitter_delay.assert_called_once_with(-250)


async def test_setting_the_dark_interval(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "number", SERVICE_SET_VALUE, {ATTR_ENTITY_ID: DARK_INTERVAL, "value": 2000}, blocking=True
    )
    mock_projector.set_3d_dark_interval.assert_called_once_with(2000)


async def test_an_out_of_range_number_is_refused(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    """Home Assistant enforces the range before the library is called."""
    mock_projector.snapshot.return_value = make_snapshot(**PACKED)
    await _setup(hass, mock_config_entry)
    with pytest.raises(ServiceValidationError, match="outside valid range 250 - 3000"):
        await hass.services.async_call(
            "number", SERVICE_SET_VALUE, {ATTR_ENTITY_ID: DARK_INTERVAL, "value": 99}, blocking=True
        )
    mock_projector.set_3d_dark_interval.assert_not_called()


async def test_invert_eyes_switch(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: INVERT}, blocking=True
    )
    mock_projector.set_3d_input_inverted.assert_called_once_with(True)
    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: INVERT}, blocking=True
    )
    mock_projector.set_3d_input_inverted.assert_called_with(False)


async def test_test_pattern_switch(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    await _setup(hass, mock_config_entry)
    await hass.services.async_call(
        "switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: TEST_PATTERN}, blocking=True
    )
    mock_projector.enable_3d_test_pattern.assert_called_once()
    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: TEST_PATTERN}, blocking=True
    )
    mock_projector.disable_3d_test_pattern.assert_called_once()


async def test_a_refused_switch_surfaces_as_home_assistant_error(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry, mock_projector
):
    mock_projector.set_3d_input_inverted.side_effect = ChristieError(105, "TDN: Disabled Control")
    await _setup(hass, mock_config_entry)
    with pytest.raises(HomeAssistantError, match="Disabled Control"):
        await hass.services.async_call(
            "switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: INVERT}, blocking=True
        )
