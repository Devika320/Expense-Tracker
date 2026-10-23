"""SQLite connection handling and schema."""
import logging
import os
import sqlite3

from flask import current_app, g

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    amount     REAL    NOT NULL CHECK (amount > 0),
    category   TEXT    NOT NULL,
    spent_on   TEXT    NOT NULL,              -- YYYY-MM-DD
    note       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_expenses_spent_on ON expenses (spent_on);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = connect(path)
    try:
        init_schema(conn)
    finally:
        conn.close()
    app.teardown_appcontext(close_db)
    logger.info("Database ready at %s", path)
