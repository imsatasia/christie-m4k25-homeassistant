"""Test the Christie M 4K25 coordinator."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.christie_m4k25.coordinator import ChristieCoordinator

from .conftest import make_snapshot


async def test_update_data_returns_snapshot(hass: HomeAssistant, mock_projector):
    """A successful poll returns the projector's Snapshot."""
    coordinator = ChristieCoordinator(hass, "192.0.2.50", 3002)

    with patch(
        "custom_components.christie_m4k25.coordinator.ChristieM4K25",
        return_value=mock_projector,
    ):
        snap = await coordinator._async_update_data()

    assert snap is mock_projector.snapshot.return_value
    mock_projector.__enter__.assert_called_once()
    mock_projector.__exit__.assert_called_once()


async def test_update_data_raises_update_failed_on_error(hass: HomeAssistant, mock_projector):
    """A read failure -- including the post-power-command blackout -- becomes
    an UpdateFailed rather than propagating a raw exception, so entities go
    unavailable for one cycle instead of the whole integration erroring."""
    mock_projector.snapshot.side_effect = TimeoutError("no reply")
    coordinator = ChristieCoordinator(hass, "192.0.2.50", 3002)

    with (
        patch(
            "custom_components.christie_m4k25.coordinator.ChristieM4K25",
            return_value=mock_projector,
        ),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()


async def test_snapshot_opens_connection_with_configured_host_and_port(
    hass: HomeAssistant, mock_projector
):
    """The coordinator connects to the host/port it was configured with."""
    coordinator = ChristieCoordinator(hass, "10.0.0.5", 4002)

    with patch(
        "custom_components.christie_m4k25.coordinator.ChristieM4K25",
        return_value=mock_projector,
    ) as mock_class:
        await coordinator._async_update_data()

    mock_class.assert_called_once_with("10.0.0.5", port=4002, timeout=8)


async def test_snapshot_field_used_by_switch_matches_fixture():
    """Sanity check that make_snapshot()'s defaults are internally consistent."""
    snap = make_snapshot()
    assert snap.is_on is True
    assert snap.shutter_open is True
