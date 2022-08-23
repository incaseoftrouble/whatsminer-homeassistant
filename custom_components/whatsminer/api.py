"""
Taken from https://github.com/satoshi-anonymoto/whatsminer-api and
https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsminerAPI%20V2.0.4.pdf
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


class WhatsminerException(BaseException):
    pass


class InvalidCommand(WhatsminerException):
    def __init__(self, message):
        super(InvalidCommand, self).__init__()
        self.message = message


class InvalidResponse(WhatsminerException):
    pass


class InvalidMessage(WhatsminerException):
    pass


class ApiPermissionDenied(WhatsminerException):
    pass


class CommandError(WhatsminerException):
    pass


class TokenError(WhatsminerException):
    pass


class TokenExceeded(WhatsminerException):
    pass


class DecodeError(WhatsminerException):
    pass


class MinerOffline(WhatsminerException):
    pass


def _check_response(message, response):
    if "STATUS" not in response:
        print(response)
        raise InvalidResponse(response)
    if response["STATUS"] == "E":
        code = response["Code"]
        if code == 14:
            raise InvalidCommand(message)
        if code == 23:
            raise InvalidMessage(message)
        if code == 45:
            raise ApiPermissionDenied(message)
        if code == 132:
            raise CommandError(message, response)
        if code == 135:
            raise TokenError()
        if code == 136:
            raise TokenExceeded()
        if code == 137:
            raise DecodeError(message)


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
        response = await r.readline()
        w.close()
        return response.decode("utf-8")

    async def _communicate(self, cmd: str, additional: Optional[Dict[str, Any]] = None, encrypted=False) -> Dict:
        if additional:
            data = dict(additional)
        else:
            data = {}
        data["cmd"] = cmd
        if encrypted:
            data["token"] = await self._get_token()

        plain_message = json.dumps(data)

        if encrypted:
            enc_str = base64.encodebytes(self._cipher.encrypt(pad(plain_message))).decode("utf-8").replace('\n', '')
            message = json.dumps({'enc': 1, 'data': enc_str})
        else:
            message = plain_message

        response = await self._communicate_raw(message)
        try:
            json_response = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response {response}") from e

        if encrypted:
            resp_plaintext: str = self._cipher.decrypt(b64decode(json_response["enc"])).decode("utf-8").rstrip('\0\n ')
            if not resp_plaintext:
                raise InvalidResponse()
            if resp_plaintext == "Socket connect failed: Connection refused":
                raise MinerOffline()
            plain_response = json.loads(resp_plaintext)
            _check_response(plain_message, plain_response)
            return plain_response

        _check_response(message, json_response)
        return json_response

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

        message = json.dumps({'cmd': 'get_token'})
        response = json.loads(await self._communicate_raw(message))
        _check_response(message, response)

        token_info = response["Msg"]
        key = crypt(self._admin_password, "$1$" + token_info["salt"] + '$').split('$')[3]
        self._cipher = AES.new(binascii.unhexlify(hashlib.sha256(key.encode()).hexdigest().encode()), AES.MODE_ECB)
        self._token = crypt(key + token_info["time"], "$1$" + token_info["newsalt"] + '$').split('$')[3]
        self._token_time = now
        return self._token

    async def read(self, cmd: str, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._communicate(cmd, additional_params, encrypted=False)

    async def write(self, cmd: str, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._communicate(cmd, additional_params, encrypted=True)

    async def check(self):
        await self._get_token()


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
