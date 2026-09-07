#!/usr/bin/env bash
pkill -f 'uvicorn backend.app.main:app' || true
