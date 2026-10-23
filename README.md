# Expense Tracker (Flask + SQLite)

A web app to record daily expenses, filter them by month and category, and see a spending breakdown.
Built as the Python Capstone Project for the Codomax internship.

**Live demo:** https://expense-tracker-a30y.onrender.com/
**Demo video:** _add your video link here_

## Features
- Add, edit and delete expenses
- Filter by month and category
- Monthly total and per-category breakdown chart
- Input validation with clear error messages (negative amounts, bad dates, unknown categories)
- Rotating log file (`logs/app.log`) and custom exceptions
- Unit tests for the business logic and routes

## Architecture
```
Browser → routes.py (HTTP) → services.py (business rules) → db.py (SQLite)
```
| File | Responsibility |
|------|----------------|
| `run.py` | Entry point (`python run.py` or `gunicorn run:app`) |
| `app/__init__.py` | App factory, error handlers, ₹ formatting filter |
| `app/config.py` | Paths, categories, limits (overridable by environment variables) |
| `app/db.py` | SQLite connection per request, schema creation |
| `app/models.py` | `Expense` dataclass |
| `app/services.py` | Validation, CRUD, filtering, summary |
| `app/routes.py` | Thin Flask views |
| `app/exceptions.py` | `ValidationError`, `InvalidAmountError`, `ExpenseNotFoundError`, ... |
| `app/logger.py` | Console + rotating file logging |
| `tests/` | Unit tests |

The services layer takes a database connection as an argument, so it is tested against an in-memory SQLite database without starting Flask.

## Database schema
Table `expenses`:

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| title | TEXT | NOT NULL |
| amount | REAL | NOT NULL, CHECK (amount > 0) |
| category | TEXT | NOT NULL |
| spent_on | TEXT | NOT NULL, format `YYYY-MM-DD`, indexed |
| note | TEXT | NOT NULL, default `''` |
| created_at | TEXT | NOT NULL, default `CURRENT_TIMESTAMP` |

## Setup
```bash
git clone <your-repo-url>
cd expense-tracker
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000

Optional environment variables: `SECRET_KEY`, `DATABASE_PATH`, `LOG_DIR`.

## Run the tests
```bash
python -m unittest discover -s tests -v
```

## Deploy on Render
1. Push the repo to GitHub.
2. On Render, create a **New Web Service** from the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app`
5. Add an environment variable `SECRET_KEY` with a long random value.

Note: on Render's free tier the filesystem is temporary, so SQLite data resets on redeploy. For permanent data, attach a persistent disk and set `DATABASE_PATH` to its mount path.

## Future improvements
- User accounts and login
- CSV export
- Monthly budgets with alerts
- Switch to PostgreSQL for hosted deployments
