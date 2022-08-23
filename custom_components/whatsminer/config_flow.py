import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac

from .api import WhatsminerAPI, ApiPermissionDenied, WhatsminerException, TokenExceeded, DecodeError, MinerOffline
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            host, port, password = user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_PASSWORD]
            api = WhatsminerAPI(host, port, password)
            try:
                await api.check()
                info = await api.read("get_miner_info", {"info": "mac"})
                version = await api.read("get_version")
            except (asyncio.TimeoutError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except DecodeError:
                errors["base"] = "invalid_auth"
            except ApiPermissionDenied:
                errors["base"] = "api_denied"
            except TokenExceeded:
                errors["base"] = "token_exceeded"
            except MinerOffline:
                errors["base"] = "miner_offline"
            except WhatsminerException:
                errors["base"] = "unknown"
            except Exception as e:
                _LOGGER.warning("Unknown error", exc_info=e)
                errors["base"] = "unknown"
            else:
                api_version: str = version["Msg"]["api_ver"]
                if not api_version.startswith("2.0"):
                    errors["base"] = "unsupported_version"
                else:
                    mac_address = format_mac(info["Msg"]["mac"])
                    await self.async_set_unique_id(mac_address)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title="Whatsminer", data={"mac": mac_address, **user_input})

        data_schema = {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=4028): int,
            vol.Required(CONF_PASSWORD): str,
        }

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)
