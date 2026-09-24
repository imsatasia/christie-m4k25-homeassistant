"""Command execution for the Christie M 4K25 integration.

Every command opens its own short-lived connection via
ChristieM4K25/hass.async_add_executor_job, the same way the coordinator's
polls do -- see coordinator.py for why the client stays synchronous rather
than being rewritten as async.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from christie_mseries import ChristieM4K25

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LENS_SETTERS: dict[str, Callable[[ChristieM4K25, int], None]] = {
    "focus": lambda projector, value: projector.set_focus(value),
    "zoom": lambda projector, value: projector.set_zoom(value),
    "horizontal": lambda projector, value: projector.set_lens_horizontal(value),
    "vertical": lambda projector, value: projector.set_lens_vertical(value),
}


class ChristieCommands:
    """Runs write commands against the projector."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize the command runner."""
        self._hass = hass
        self._host = host
        self._port = port

    async def _async_run(self, action: Callable[[ChristieM4K25], None]) -> None:
        """Run a blocking action against a short-lived connection."""
        await self._hass.async_add_executor_job(self._run, action)

    def _run(self, action: Callable[[ChristieM4K25], None]) -> None:
        with ChristieM4K25(self._host, port=self._port, timeout=10) as projector:
            action(projector)

    async def async_power_on(self) -> None:
        """Turn the projector on."""
        await self._async_run(lambda projector: projector.power_on())

    async def async_power_off(self) -> None:
        """Set the projector to standby."""
        await self._async_run(lambda projector: projector.power_off())

    async def async_open_shutter(self) -> None:
        """Open the mechanical shutter."""
        await self._async_run(lambda projector: projector.open_shutter())

    async def async_close_shutter(self) -> None:
        """Close the mechanical shutter."""
        await self._async_run(lambda projector: projector.close_shutter())

    async def async_select_input(self, source: int | str) -> None:
        """Switch the active video input, by SIN index or port label."""
        await self._async_run(lambda projector: projector.select_input(source))

    async def async_set_brightness(self, percent: float) -> None:
        """Set light-source brightness, 30.0-100.0."""
        await self._async_run(lambda projector: projector.set_brightness(percent))

    async def async_set_test_pattern(self, pattern: int | str) -> None:
        """Display an internal test pattern, by value or by name."""
        await self._async_run(lambda projector: projector.set_test_pattern(pattern))

    async def async_set_liteloc(self, enabled: bool) -> None:
        """Enable or disable LiteLOC."""
        await self._async_run(lambda projector: projector.set_liteloc(enabled))

    async def async_set_lens_position(self, axis: str, position: int) -> None:
        """Move one lens axis to an absolute motor position.

        Refused by the projector with "Disabled Control" unless it's on --
        that's surfaced as a HomeAssistantError from the entity layer rather
        than pre-checked here, the same way every other rejected command is.
        """
        setter = _LENS_SETTERS[axis]
        await self._async_run(lambda projector: setter(projector, position))

    async def async_raw_set(self, code: str, subcode: str | None, data: object) -> None:
        """Escape hatch: send a raw SET for any code not wrapped above."""
        await self._async_run(lambda projector: projector.raw_set(code, subcode=subcode, data=data))

    async def async_raw_query(self, code: str, subcode: str | None) -> str:
        """Escape hatch: send a raw REQUEST and return the reply data."""
        return await self._hass.async_add_executor_job(self._raw_query, code, subcode)

    def _raw_query(self, code: str, subcode: str | None) -> str:
        with ChristieM4K25(self._host, port=self._port, timeout=10) as projector:
            return projector.raw_query(code, subcode=subcode)
