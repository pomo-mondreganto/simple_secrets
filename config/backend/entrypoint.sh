#!/bin/sh

#/await_start.sh

set -e

cd /app/
echo "[*] Starting web api"
gunicorn app:app --bind 0.0.0.0:5000 --worker-class sanic.worker.GunicornWorker
#python app.py
