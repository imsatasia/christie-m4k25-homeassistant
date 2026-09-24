"""Config flow for the Christie M 4K25 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from christie_mseries import ChristieM4K25
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers import config_validation as cv

from .const import CONF_PORT, DEFAULT_PORT, DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


class ChristieConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Christie M 4K25."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            try:
                await self.hass.async_add_executor_job(_probe, host, port)
            except OSError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during Christie M 4K25 setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{NAME} ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)


def _probe(host: str, port: int) -> None:
    """Blocking: confirm the projector answers on its serial API port."""
    with ChristieM4K25(host, port=port, timeout=8) as projector:
        projector.get_power_state_text()
