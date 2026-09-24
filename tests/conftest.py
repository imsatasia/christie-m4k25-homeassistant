"""Fixtures for the Christie M 4K25 integration tests."""

from unittest.mock import MagicMock, patch

import pytest
from christie_mseries import Snapshot
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.christie_m4k25.const import CONF_PORT, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


def get_state(hass: HomeAssistant, entity_id: str) -> State:
    """Return an entity's state, asserting it exists (a clearer failure than
    a None attribute error, and a type-narrowed return for ty)."""
    state = hass.states.get(entity_id)
    assert state, f"no state for {entity_id}"
    return state


def make_snapshot(**overrides) -> Snapshot:
    """Build a Snapshot with sensible defaults, overriding only what a test cares about."""
    defaults = {
        "power": "On",
        "power_code": 1,
        "is_on": True,
        "in_transition": False,
        "shutter_open": True,
        "input": 1,
        "input_name": "One-Port HDMI0",
        "input_label": "HDMI 2.0 Port 1",
        "inputs": ["HDMI 2.0 Port 1", "HDMI 2.0 Port 2", "HDMI 2.1 Port 3"],
        "input_map": {"HDMI 2.0 Port 1": 1, "HDMI 2.0 Port 2": 2, "HDMI 2.1 Port 3": 3},
        "hours": "3:14 (h:m)",
        "model": "Christie M 4K25 RGB",
        "serial": "12345",
        "alarms": 0,
        "brightness": 70.0,
        "liteloc": True,
        "test_pattern": "Off",
        "test_patterns": ["Off", "Grid", "Color Bars"],
        "test_pattern_map": {"Off": 0, "Grid": 1, "Color Bars": 9},
        "focus": 1100,
        "zoom": -267,
        "lens_horizontal": -1032,
        "lens_vertical": -1417,
        "intake_temp": 32.0,
    }
    defaults.update(overrides)
    return Snapshot(**defaults)


@pytest.fixture
def mock_projector():
    """Create a mock ChristieM4K25 instance, as returned by the ChristieM4K25(...) constructor."""
    projector = MagicMock()
    projector.__enter__ = MagicMock(return_value=projector)
    projector.__exit__ = MagicMock(return_value=False)
    projector.snapshot = MagicMock(return_value=make_snapshot())
    projector.get_power_state_text = MagicMock(return_value="On")
    return projector


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Christie M 4K25 RGB (192.0.2.50)",
        data={CONF_HOST: "192.0.2.50", CONF_PORT: 3002},
        unique_id="192.0.2.50:3002",
    )


@pytest.fixture
def mock_setup_entry(mock_projector):
    """Patch ChristieM4K25 everywhere this integration imports it from."""
    with (
        patch(
            "custom_components.christie_m4k25.coordinator.ChristieM4K25",
            return_value=mock_projector,
        ) as mock_coordinator_class,
        patch(
            "custom_components.christie_m4k25.commands.ChristieM4K25",
            return_value=mock_projector,
        ),
        patch(
            "custom_components.christie_m4k25.config_flow.ChristieM4K25",
            return_value=mock_projector,
        ),
    ):
        yield mock_coordinator_class
