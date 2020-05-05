import hashlib
import hmac
import secrets

from Crypto.Cipher import AES
from sanic import Sanic

import exceptions


def get_aes_key(app: Sanic, passphrase: str) -> bytes:
    """Combine app.secret_key and passphrase, cut by BS length."""
    salted = (passphrase + app.secret_key).encode()
    return hashlib.sha256(salted).digest()[:AES.block_size]


def pad(s: bytes) -> bytes:
    """Pad 16-byte data for AES."""
    return s + bytes([16 - len(s) % 16]) * (16 - len(s) % 16)


def unpad(s: bytes) -> bytes:
    """Unpad 16-byte data from AES."""
    return s[:-s[-1]]


async def add_secret(app: Sanic, secret: str, passphrase: str) -> str:
    """
    Add a secret to app.db.

    :param app: Sanic app
    :param secret: secret to add
    :param passphrase: passphrase associated with a secret
    :return: secret key to acquire secret afterwards
    """

    key = get_aes_key(app, passphrase)

    sign = hmac.digest(key=key, msg=passphrase.encode(), digest='sha512').hex()
    secret_key = secrets.token_hex(16)
    iv = secrets.token_bytes(16)

    cipher = AES.new(key=pad(key), mode=AES.MODE_CBC, iv=iv)
    encrypted = iv.hex() + cipher.encrypt(pad(secret.encode())).hex()

    await app.db.secrets.insert_one({
        'secret': encrypted,
        'secret_key': secret_key,
        'signature': sign,
    })

    return secret_key


async def get_secret(app: Sanic, secret_key: str, passphrase: str) -> str:
    """
    Get a secret from app.db, validating it.

    :param app: Sanic application
    :param secret_key: secret key associated with a secret
    :param passphrase: passphrase associated with a secret
    :return: secret
    :raises InvalidPassphraseException: is passphrase is invalid
    :raises InvalidSecretKeyException: is secret_key is invalid
    """

    data = await app.db.secrets.find_one({'secret_key': secret_key})
    await app.db.secrets.find_one({'secret_key': secret_key})
    if not data:
        raise exceptions.InvalidSecretKeyException()

    key = get_aes_key(app, passphrase)

    sign = hmac.digest(key=key, msg=passphrase.encode(), digest='sha512').hex()
    if sign != data['signature']:
        raise exceptions.InvalidPassphraseException()

    await app.db.secrets.delete_one({'secret_key': secret_key})

    iv = b''.fromhex(data['secret'][:32])
    encrypted = b''.fromhex(data['secret'][32:])
    cipher = AES.new(key=pad(key), mode=AES.MODE_CBC, iv=iv)
    secret = unpad(cipher.decrypt(encrypted)).decode()

    return secret
