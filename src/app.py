import os

from motor.motor_asyncio import AsyncIOMotorClient
from sanic import Sanic
from sanic.response import json

import controllers
import exceptions

app = Sanic('simple_secrets')
app.secret_key = os.environ['BACKEND_SECRET_KEY']

MAX_TTL = 60 * 60 * 24


def get_db_client():
    if os.environ.get('TRAVIS'):
        conn_url = f'mongodb://127.0.0.1:27017/'
    else:  # pragma: no cover
        mongo_host = os.environ.get('MONGO_HOST', '127.0.0.1')
        mongo_username = os.environ['MONGO_INITDB_ROOT_USERNAME']
        mongo_password = os.environ['MONGO_INITDB_ROOT_PASSWORD']
        conn_url = f'mongodb://{mongo_username}:{mongo_password}@{mongo_host}:27017/'

    client = AsyncIOMotorClient(conn_url)
    return client


@app.listener('before_server_start')
def init_db(sanic, _loop):
    client = get_db_client()
    sanic.db = client.simple_secrets
    sanic.db.secrets.create_index([("expires", 1)], expireAfterSeconds=0)


def make_error_response(error, status=400):
    return json({'error': error}, status=status)


@app.route('/generate/', methods=['POST'])
async def generate(request):
    """
    A route to generate secret key by secret & passphrase (in JSON).

    ttl can be passed optionally
    """
    try:
        secret = request.json.get('secret')
        passphrase = request.json.get('passphrase')
        ttl = request.json.get('ttl')
        if ttl:
            ttl = int(ttl)
    except AttributeError:
        return make_error_response('valid json required')
    except ValueError:
        return make_error_response('ttl must be an integer')

    if ttl and (ttl < 0 or ttl > MAX_TTL):  # a day
        return make_error_response(f'ttl must be a non-negative integer less or equal to {MAX_TTL}')

    if not secret or not passphrase:
        return make_error_response('both secret and passphrase are required')

    secret_key = await controllers.add_secret(app, secret, passphrase, ttl)

    return json({'secret_key': secret_key})


@app.route('/secret/<secret_key>/', methods=['POST'])
async def get_secret(request, secret_key):
    """Get secret by secret_key (in url) and passphrase (in json)."""
    try:
        passphrase = request.json.get('passphrase')
    except AttributeError:
        return make_error_response('valid json required')

    if not passphrase:
        return make_error_response('passphrase is required')

    try:
        secret = await controllers.get_secret(app, secret_key, passphrase)
    except exceptions.InvalidPassphraseException:
        return make_error_response('invalid passphrase')
    except exceptions.InvalidSecretKeyException:
        return make_error_response('no such secret')

    return json({'secret': secret})


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=True, port=5000, host='0.0.0.0')
