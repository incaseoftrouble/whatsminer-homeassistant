import asyncio
import json
import logging
from typing import Optional, Any, Tuple, Dict

import aiohttp
import voluptuous as vol
import whatsminer
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac

from .const import TOKEN, DOMAIN, CONF_HOST, CONF_PORT, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)


async def create_and_validate_token(host, port, password) -> Tuple[whatsminer.WhatsminerAccessToken, Dict]:
    token = whatsminer.WhatsminerAccessToken(host, port, password)
    return token, whatsminer.WhatsminerAPI.get_read_only_info(token, "summary")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            host, port, password = user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_PASSWORD]
            try:
                token, summary = await create_and_validate_token(host, port, password)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except json.JSONDecodeError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
            else:
                mac_address = format_mac(summary["mac"])
                await self.async_set_unique_id(mac_address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title="Whatsminer", data={TOKEN: token})

        data_schema = {
            vol.Required("host"): str,
            vol.Optional("port", default=4028): int,
            vol.Required("password"): str,
        }

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)
