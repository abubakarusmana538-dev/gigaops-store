"""Gunicorn entrypoint: initialise the DB once (with --preload), then serve."""
from app import app, initialize_db

initialize_db()

__all__ = ["app"]
