#!/usr/bin/env bash
set -e
python3 -m pip install -r requirements.txt
python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
