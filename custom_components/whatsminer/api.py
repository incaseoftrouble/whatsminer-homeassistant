"""
Taken from https://github.com/satoshi-anonymoto/whatsminer-api
"""
import asyncio
import base64
import binascii
import datetime
import hashlib
import json
import logging
import re
from base64 import b64decode
from typing import Any, Dict, Optional

from Crypto.Cipher import AES
from passlib.hash import md5_crypt

logger = logging.getLogger(__name__)


class WhatsminerAPI(object):
    def __init__(self, host: str, port: int = 4028, admin_password: str = None):
        self.host = host
        self.port = port
        self._admin_password = admin_password
        self._token = None
        self._token_time = None
        self._cipher = None

    async def _communicate_raw(self, data: str) -> str:
        r, w = await asyncio.open_connection(host=self.host, port=self.port)
        w.write(data.encode('utf-8'))
        w.close()
        return (await r.read()).decode("utf-8")

    async def _communicate(self, cmd: str, additional: Optional[Dict[str, Any]] = None, encrypted=False) -> Dict:
        if additional:
            data = dict(additional)
        else:
            data = {}
        data["cmd"] = cmd
        if encrypted:
            data["token"] = await self._get_token()

        msg = json.dumps(data)

        if encrypted:
            enc_str = str(base64.encodebytes(self._cipher.encrypt(pad(msg))), encoding='utf8').replace('\n', '')
            msg = json.dumps({'enc': 1, 'data': enc_str})

        response = json.loads(await self._communicate_raw(msg))
        if "STATUS" in response and response["STATUS"] == "E":
            logger.error(response["Msg"])
            raise Exception(msg + "\n" + response["Msg"])

        if encrypted:
            resp_ciphertext = b64decode(response["enc"])
            resp_plaintext = self._cipher.decrypt(resp_ciphertext).decode().split("\x00")[0]
            return json.loads(resp_plaintext)
        return response

    async def _get_token(self) -> str:
        """
        Encryption algorithm:
        Ciphertext = aes256(plaintext)，ECB mode
        Encode text = base64(ciphertext)

        (1)api_cmd = token,$sign|api_str    # api_str is API command plaintext
        (2)enc_str = aes256(api_cmd, $key)  # ECB mode
        (3)tran_str = base64(enc_str)

        Final assembly: enc|base64(aes256("token,sign|set_led|auto", $aes_key))
        """

        now = datetime.datetime.now()

        if self._token_time is not None and (now - self._token_time).total_seconds() < 29 * 60:
            return self._token

        response = json.loads(await self._communicate_raw(json.dumps({'cmd': 'get_token'})))
        token_info = response["Msg"]
        if token_info == "over max connect":
            raise Exception(response)

        key = crypt(self._admin_password, "$1$" + token_info["salt"] + '$').split('$')[3]
        self._cipher = AES.new(binascii.unhexlify(hashlib.sha256(key.encode()).hexdigest().encode()), AES.MODE_ECB)
        self._token = crypt(key + token_info["time"], "$1$" + token_info["newsalt"] + '$').split('$')[3]
        self._token_time = now
        return self._token

    async def read(self, cmd: str, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._communicate(cmd, additional_params, encrypted=False)

    async def write(self, cmd: str, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._communicate(cmd, additional_params, encrypted=True)


# ================================ misc helpers ================================
def crypt(word, salt):
    standard_salt = re.compile('\\s*\\$(\\d+)\\$([\\w./]*)\\$')
    match = standard_salt.match(salt)
    if not match:
        raise ValueError("salt format is not correct")
    extra_str = match.group(2)
    result = md5_crypt.hash(word, salt=extra_str)
    return result


def pad(s):
    if len(s) % 16:
        s += '\0' * (16 - len(s) % 16)
    return str.encode(s, "utf-8")
