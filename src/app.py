import os

from motor.motor_asyncio import AsyncIOMotorClient
from sanic import Sanic
from sanic.response import json

import controllers
import exceptions

app = Sanic('avito_entry')
app.secret_key = os.environ['BACKEND_SECRET_KEY']


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
def init_db(_sanic, _loop):
    client = get_db_client()
    app.db = client.avito_entry


def make_error_response(error, status=400):
    return json({'error': error}, status=status)


@app.route('/generate/', methods=['POST'])
async def generate(request):
    """A route to generate secret key

    secret & passphrase need to be provided in json
    """
    try:
        secret = request.json.get('secret')
        passphrase = request.json.get('passphrase')
    except AttributeError:
        return make_error_response('valid json required')

    if not secret or not passphrase:
        return make_error_response('both secret and passphrase are required')

    secret_key = await controllers.add_secret(app, secret, passphrase)

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
