"""Business logic. Works on any sqlite3 connection (easy to test)."""
import logging
from datetime import date, datetime

from . import config
from .exceptions import (
    ExpenseNotFoundError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    ValidationError,
)
from .models import Expense

logger = logging.getLogger(__name__)


def validate(title, amount, category, spent_on, note=""):
    """Clean and validate form input. Raises a ValidationError subclass."""
    title = (title or "").strip()
    if not title:
        raise ValidationError("Title is required.")
    if len(title) > 100:
        raise ValidationError("Title must be 100 characters or fewer.")

    try:
        amount = round(float(amount), 2)
    except (TypeError, ValueError):
        raise InvalidAmountError("Amount must be a number, for example 250 or 99.50.")
    if amount != amount or amount in (float("inf"), float("-inf")):
        raise InvalidAmountError("Amount must be a number, for example 250 or 99.50.")
    if amount <= 0:
        raise InvalidAmountError("Amount must be greater than zero.")
    if amount > config.MAX_AMOUNT:
        raise InvalidAmountError("Amount is too large.")

    if category not in config.CATEGORIES:
        raise InvalidCategoryError("Pick a category from the list.")

    try:
        parsed = datetime.strptime(spent_on or "", "%Y-%m-%d").date()
    except ValueError:
        raise InvalidDateError("Date must look like 2026-10-23.")
    if parsed > date.today():
        raise InvalidDateError("Date cannot be in the future.")

    return {
        "title": title,
        "amount": amount,
        "category": category,
        "spent_on": parsed.isoformat(),
        "note": (note or "").strip()[:300],
    }


def add_expense(conn, title, amount, category, spent_on, note=""):
    data = validate(title, amount, category, spent_on, note)
    cur = conn.execute(
        "INSERT INTO expenses (title, amount, category, spent_on, note) VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["amount"], data["category"], data["spent_on"], data["note"]),
    )
    conn.commit()
    logger.info("Added expense id=%s amount=%.2f category=%s", cur.lastrowid, data["amount"], data["category"])
    return cur.lastrowid


def get_expense(conn, expense_id):
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist.")
    return Expense.from_row(row)


def list_expenses(conn, month=None, category=None):
    """month is 'YYYY-MM' or None for all time."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        query += " AND substr(spent_on, 1, 7) = ?"
        params.append(month)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY spent_on DESC, id DESC"
    return [Expense.from_row(r) for r in conn.execute(query, params).fetchall()]


def update_expense(conn, expense_id, title, amount, category, spent_on, note=""):
    get_expense(conn, expense_id)  # raises if missing
    data = validate(title, amount, category, spent_on, note)
    conn.execute(
        "UPDATE expenses SET title=?, amount=?, category=?, spent_on=?, note=? WHERE id=?",
        (data["title"], data["amount"], data["category"], data["spent_on"], data["note"], expense_id),
    )
    conn.commit()
    logger.info("Updated expense id=%s", expense_id)


def delete_expense(conn, expense_id):
    get_expense(conn, expense_id)  # raises if missing
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    logger.info("Deleted expense id=%s", expense_id)


def summary(conn, month=None):
    """Total, count and per-category totals (highest first)."""
    where, params = "", []
    if month:
        where, params = "WHERE substr(spent_on, 1, 7) = ?", [month]
    total_row = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS n FROM expenses {where}", params
    ).fetchone()
    rows = conn.execute(
        f"SELECT category, SUM(amount) AS total FROM expenses {where} GROUP BY category ORDER BY total DESC",
        params,
    ).fetchall()
    total = total_row["total"]
    by_category = [
        {"category": r["category"], "total": r["total"], "percent": round(r["total"] / total * 100) if total else 0}
        for r in rows
    ]
    return {"total": total, "count": total_row["n"], "by_category": by_category}
