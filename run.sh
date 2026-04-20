#!/usr/bin/env bash
set -e

VENV=".venv"

if [ ! -d "$VENV" ]; then
  echo "Virtuele omgeving aanmaken…"
  python3 -m venv "$VENV"
fi

echo "Afhankelijkheden installeren…"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements.txt

echo "App starten op http://localhost:5000"
"$VENV/bin/python" app.py
