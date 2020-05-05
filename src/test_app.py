from app import app, make_error_response


def simple_add_secret(secret, passphrase) -> str:
    _, response = app.test_client.post(
        '/generate/',
        json={
            'secret': secret,
            'passphrase': passphrase,
        },
    )
    data = response.json
    secret_key = data['secret_key']
    return secret_key


def test_simple_generate():
    secret = 'my_secret'
    passphrase = 'passphrase'
    _, response = app.test_client.post(
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
    secret_key = simple_add_secret(secret, passphrase)

    _, response = app.test_client.post(
        f'/secret/{secret_key}/',
        json={'passphrase': passphrase},
    )
    assert response.status == 200
    data = response.json
    assert data.get('secret') == secret


def test_invalid_passphrase():
    secret = 'my_secret'
    passphrase = 'passphrase'
    secret_key = simple_add_secret(secret, passphrase)

    _, response = app.test_client.post(
        f'/secret/{secret_key}/',
        json={'passphrase': 'invalid passphrase'},
    )
    assert response.status != 200
    data = response.json
    assert bool(data.get('error'))


def test_invalid_secret_key():
    secret = 'my_secret'
    passphrase = 'passphrase'
    simple_add_secret(secret, passphrase)

    _, response = app.test_client.post(
        f'/secret/invalid_secret_key/',
        json={'passphrase': passphrase},
    )
    assert response.status != 200
    data = response.json
    assert bool(data.get('error'))


def test_generate_invalid_json():
    _, response = app.test_client.post(f'/generate/')
    assert response.status != 200


def test_generate_no_passphrase_or_secret():
    _, response = app.test_client.post(f'/generate/', json={'secret': 'kek', 'no': 'passphrase'})
    assert response.status != 200

    _, response = app.test_client.post(f'/generate/', json={'passphrase': 'kek', 'no': 'secret'})
    assert response.status != 200


def test_get_secret_invalid_json():
    _, response = app.test_client.post(f'/secret/1234/')
    assert response.status != 200


def test_get_secret_no_passphrase():
    _, response = app.test_client.post(f'/secret/123456534/', json={'secret': 'kek', 'no': 'passphrase'})
    assert response.status != 200


def test_error_response():
    response = make_error_response('some error', status=419)
    assert response.status == 419
    assert response.content_type == 'application/json'
    assert b'some error' in response.body
