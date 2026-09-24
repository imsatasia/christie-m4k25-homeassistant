"""Test the Christie M 4K25 config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.christie_m4k25.const import DOMAIN


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_projector):
    """A successful probe creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "custom_components.christie_m4k25.config_flow.ChristieM4K25",
        return_value=mock_projector,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.0.2.50", "port": 3002}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Christie M 4K25 RGB (192.0.2.50)"
    assert result["data"] == {"host": "192.0.2.50", "port": 3002}


async def test_user_flow_cannot_connect(hass: HomeAssistant):
    """A connection failure is shown as a form error, not raised."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.christie_m4k25.config_flow.ChristieM4K25",
        side_effect=OSError("Connection refused"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.0.2.50", "port": 3002}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_aborts_on_duplicate(hass: HomeAssistant, mock_projector):
    """A second entry for the same host:port aborts as already configured."""
    with patch(
        "custom_components.christie_m4k25.config_flow.ChristieM4K25",
        return_value=mock_projector,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.0.2.50", "port": 3002}
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.0.2.50", "port": 3002}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
