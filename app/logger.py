"""Logging setup: console + rotating file."""
import logging
import os
from logging.handlers import RotatingFileHandler

from . import config


def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(h, "_expense_handler", False) for h in root.handlers):
        return  # already configured

    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(config.LOG_DIR, "app.log"), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    console = logging.StreamHandler()
    for h in (file_handler, console):
        h.setFormatter(fmt)
        h._expense_handler = True
        root.addHandler(h)
    root.setLevel(logging.INFO)
