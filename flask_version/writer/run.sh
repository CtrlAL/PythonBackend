#!/bin/sh
python -c "from app import app, db; with app.app_context(): db.create_all()"
exec python -m flask --app app run --host=0.0.0.0 --port=5000
