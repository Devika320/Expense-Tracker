"""HTTP routes (thin: parse request, call services, render)."""
import logging
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import config, services
from .db import get_db
from .exceptions import ExpenseNotFoundError, ValidationError

logger = logging.getLogger(__name__)
bp = Blueprint("expenses", __name__)

FORM_FIELDS = ("title", "amount", "category", "spent_on", "note")


def _form_values():
    return {f: request.form.get(f, "") for f in FORM_FIELDS}


@bp.route("/")
def index():
    month = request.args.get("month", date.today().strftime("%Y-%m"))  # "" means all time
    category = request.args.get("category", "")
    db = get_db()
    return render_template(
        "index.html",
        expenses=services.list_expenses(db, month or None, category or None),
        summary=services.summary(db, month or None),
        month=month,
        category=category,
        categories=config.CATEGORIES,
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    values = {"spent_on": date.today().isoformat(), "category": config.CATEGORIES[0]}
    if request.method == "POST":
        values = _form_values()
        try:
            services.add_expense(get_db(), **values)
            flash("Expense added.", "ok")
            return redirect(url_for("expenses.index"))
        except ValidationError as err:
            logger.warning("Rejected new expense: %s", err)
            flash(str(err), "error")
    return render_template("form.html", values=values, categories=config.CATEGORIES, editing=False)


@bp.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id):
    db = get_db()
    try:
        expense = services.get_expense(db, expense_id)
    except ExpenseNotFoundError:
        flash("That expense no longer exists.", "error")
        return redirect(url_for("expenses.index"))

    values = vars(expense).copy()
    if request.method == "POST":
        values = _form_values()
        try:
            services.update_expense(db, expense_id, **values)
            flash("Changes saved.", "ok")
            return redirect(url_for("expenses.index"))
        except ValidationError as err:
            logger.warning("Rejected edit of expense %s: %s", expense_id, err)
            flash(str(err), "error")
    return render_template("form.html", values=values, categories=config.CATEGORIES, editing=True)


@bp.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    try:
        services.delete_expense(get_db(), expense_id)
        flash("Expense deleted.", "ok")
    except ExpenseNotFoundError:
        flash("That expense no longer exists.", "error")
    return redirect(url_for("expenses.index"))
