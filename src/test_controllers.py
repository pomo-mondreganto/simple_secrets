import controllers
from app import app, get_db_client


def test_pad():
    s = 'abacaba'
    assert controllers.pad(s.encode()) == b'abacaba' + b'\x09' * 9


def test_unpad():
    s = b'abacaba'
    assert controllers.unpad(controllers.pad(s)) == s


async def test_add_secret():
    app.db = get_db_client().simple_secrets
    secret = 'my_secret'
    passphrase = 'passphrase'
    secret_key = await controllers.add_secret(app, secret, passphrase)
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
    secret_key = await controllers.add_secret(app, secret, passphrase)

    new_secret = await controllers.get_secret(app, secret_key, passphrase)
    assert secret == new_secret
