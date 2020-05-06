import time

import controllers
import exceptions
from app import app, get_db_client


async def test_add_secret():
    app.db = get_db_client().simple_secrets
    secret = 'my_secret'
    passphrase = 'passphrase'
    ttl = None
    secret_key = await controllers.add_secret(app, secret, passphrase, ttl)
    data = await app.db.secrets.find_one({
        'secret_key': secret_key,
    })

    assert bool(data)
    assert 'secret' in data
    assert 'secret_key' in data
    assert 'signature' in data
    assert data['secret'] != secret


async def test_get_secret():
    app.db = get_db_client().simple_secrets
    secret = 'my_secret'
    passphrase = 'passphrase'
    ttl = None
    secret_key = await controllers.add_secret(app, secret, passphrase, ttl)

    new_secret = await controllers.get_secret(app, secret_key, passphrase)
    assert secret == new_secret


async def test_limit_expired():
    app.db = get_db_client().simple_secrets
    secret = 'my_secret'
    passphrase = 'passphrase'
    ttl = 2
    secret_key = await controllers.add_secret(app, secret, passphrase, ttl)
    time.sleep(5)
    try:
        await controllers.get_secret(app, secret_key, passphrase)
    except exceptions.InvalidSecretKeyException:
        pass
    else:
        assert False, 'TTL not working'
