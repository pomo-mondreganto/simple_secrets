import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from cryptography import fernet
from sanic import Sanic

import exceptions


def get_fernet_key(app: Sanic, passphrase: str) -> bytes:
    """Combine app.secret_key and passphrase, cut by key length."""
    salted = (passphrase + app.secret_key).encode()
    key = hashlib.sha256(salted).digest()[:32]
    return base64.urlsafe_b64encode(key)


async def add_secret(app: Sanic, secret: str, passphrase: str, ttl: Optional[int]) -> str:
    """
    Add a secret to app.db.

    :param app: Sanic app
    :param secret: secret to add
    :param passphrase: passphrase associated with a secret
    :param ttl: secret time to live (optional)
    :return: secret key to acquire secret afterwards
    """

    key = get_fernet_key(app, passphrase)

    sign = hmac.digest(key=key, msg=passphrase.encode(), digest='sha512').hex()
    secret_key = secrets.token_hex(16)

    cipher = fernet.Fernet(key)
    encrypted = cipher.encrypt(secret.encode()).decode()

    expires = None
    if ttl:
        expires = datetime.utcnow() + timedelta(seconds=ttl)

    await app.db.secrets.insert_one({
        'secret': encrypted,
        'secret_key': secret_key,
        'signature': sign,
        'expires': expires,  # for mongo index
        'ttl': ttl,  # for fernet check
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

    key = get_fernet_key(app, passphrase)

    sign = hmac.digest(key=key, msg=passphrase.encode(), digest='sha512').hex()
    if sign != data['signature']:
        raise exceptions.InvalidPassphraseException()

    await app.db.secrets.delete_one({'secret_key': secret_key})

    encrypted = data['secret'].encode()
    cipher = fernet.Fernet(key)
    if data.get('ttl'):
        try:
            secret = cipher.decrypt(encrypted, ttl=data['ttl']).decode()
        except fernet.InvalidToken:
            raise exceptions.InvalidSecretKeyException()
    else:
        secret = cipher.decrypt(encrypted).decode()

    return secret
