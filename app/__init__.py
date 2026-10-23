"""Flask application factory."""
import logging

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from . import config, db
from .logger import setup_logging


def create_app(test_config=None):
    setup_logging()
    log = logging.getLogger(__name__)

    app = Flask(__name__)
    app.config.update(SECRET_KEY=config.SECRET_KEY, DATABASE_PATH=config.DATABASE_PATH)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    @app.template_filter("inr")
    def inr(value):
        return f"₹{value:,.2f}"

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="We couldn't find that page."), 404

    @app.errorhandler(Exception)
    def unexpected(e):
        if isinstance(e, HTTPException):
            return e
        log.exception("Unhandled error: %s", e)
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500

    log.info("App started")
    return app
