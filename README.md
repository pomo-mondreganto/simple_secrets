[![Build Status](https://travis-ci.com/pomo-mondreganto/simple_secrets.svg?branch=master)](https://travis-ci.com/pomo-mondreganto/simple_secrets)

# simple_secrets

It's a simple secrets storage app with the following functions:

- save a secret: make a `POST` request to `/generate/`, sending 
`secret` and `passphrase` in JSON, receive the `secret_key` as the answer.
- fetch a secret (each secret can be fetched only once): `POST` request to `/secret/<secret_key>/`,
sending `passphrase` in JSON, receive the `secret` as the answer.

Neither secret nor passphrase are stored on server in plaintext. Secret is encrypted with AES CBC, and 
passphrase is HMACed.  

It's written in Sanic with MongoDB as the storage.
