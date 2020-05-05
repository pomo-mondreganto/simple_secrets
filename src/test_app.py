from app import app, make_error_response


def test_simple_generate():
    secret = 'my_secret'
    passphrase = 'passphrase'
    request, response = app.test_client.post(
        '/generate/',
        json={
            'secret': secret,
            'passphrase': passphrase,
        },
    )
    assert response.status == 200
    data = response.json
    assert bool(data.get('secret_key'))


def test_simple_get_secret():
    secret = 'my_secret'
    passphrase = 'passphrase'
    request, response = app.test_client.post(
        '/generate/',
        json={
            'secret': secret,
            'passphrase': passphrase,
        },
    )
    data = response.json
    secret_key = data['secret_key']

    request, response = app.test_client.post(
        f'/secret/{secret_key}/',
        json={'passphrase': passphrase},
    )
    assert response.status == 200
    data = response.json
    assert data.get('secret') == secret


def test_invalid_passphrase():
    secret = 'my_secret'
    passphrase = 'passphrase'
    request, response = app.test_client.post(
        '/generate/',
        json={
            'secret': secret,
            'passphrase': passphrase,
        },
    )
    data = response.json
    secret_key = data['secret_key']

    request, response = app.test_client.post(
        f'/secret/{secret_key}/',
        json={'passphrase': 'invalid passphrase'},
    )
    assert response.status != 200
    data = response.json
    assert bool(data.get('error'))


def test_invalid_secret_key():
    secret = 'my_secret'
    passphrase = 'passphrase'

    app.test_client.post(
        '/generate/',
        json={
            'secret': secret,
            'passphrase': passphrase,
        },
    )

    request, response = app.test_client.post(
        f'/secret/invalid_secret_key/',
        json={'passphrase': passphrase},
    )
    assert response.status != 200
    data = response.json
    assert bool(data.get('error'))


def test_error_response():
    response = make_error_response('some error', status=419)
    assert response.status == 419
    assert response.content_type == 'application/json'
    assert b'some error' in response.body
