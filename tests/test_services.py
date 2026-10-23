import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db, services  # noqa: E402
from app.exceptions import (  # noqa: E402
    ExpenseNotFoundError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
    ValidationError,
)

TODAY = date.today().isoformat()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_add_and_get(self):
        eid = services.add_expense(self.conn, "Lunch", "120.50", "Food", TODAY)
        e = services.get_expense(self.conn, eid)
        self.assertEqual((e.title, e.amount, e.category), ("Lunch", 120.5, "Food"))

    def test_rejects_bad_amounts(self):
        for bad in ("-5", "0", "abc", "", "nan", "inf"):
            with self.assertRaises(InvalidAmountError, msg=bad):
                services.add_expense(self.conn, "X", bad, "Food", TODAY)

    def test_rejects_bad_category_date_title(self):
        with self.assertRaises(InvalidCategoryError):
            services.add_expense(self.conn, "X", "10", "Nope", TODAY)
        with self.assertRaises(InvalidDateError):
            services.add_expense(self.conn, "X", "10", "Food", "23-10-2026")
        future = (date.today() + timedelta(days=2)).isoformat()
        with self.assertRaises(InvalidDateError):
            services.add_expense(self.conn, "X", "10", "Food", future)
        with self.assertRaises(ValidationError):
            services.add_expense(self.conn, "   ", "10", "Food", TODAY)

    def test_update_and_delete(self):
        eid = services.add_expense(self.conn, "Bus", "30", "Transport", TODAY)
        services.update_expense(self.conn, eid, "Metro", "45", "Transport", TODAY)
        self.assertEqual(services.get_expense(self.conn, eid).title, "Metro")
        services.delete_expense(self.conn, eid)
        with self.assertRaises(ExpenseNotFoundError):
            services.get_expense(self.conn, eid)

    def test_filters_and_summary(self):
        services.add_expense(self.conn, "A", "100", "Food", "2026-01-10")
        services.add_expense(self.conn, "B", "300", "Bills", "2026-01-15")
        services.add_expense(self.conn, "C", "50", "Food", "2026-02-01")
        self.assertEqual(len(services.list_expenses(self.conn, month="2026-01")), 2)
        self.assertEqual(len(services.list_expenses(self.conn, category="Food")), 2)
        s = services.summary(self.conn, "2026-01")
        self.assertEqual((s["total"], s["count"]), (400, 2))
        self.assertEqual(s["by_category"][0]["category"], "Bills")
        self.assertEqual(s["by_category"][0]["percent"], 75)

    def test_empty_summary(self):
        s = services.summary(self.conn, "2020-01")
        self.assertEqual((s["total"], s["count"], s["by_category"]), (0, 0, []))


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE_PATH": os.path.join(self.tmp.name, "t.db")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_pages_load(self):
        for path in ("/", "/add"):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get("/nope").status_code, 404)

    def test_add_flow_and_error_message(self):
        r = self.client.post("/add", data={"title": "Tea", "amount": "-1", "category": "Food", "spent_on": TODAY})
        self.assertIn(b"greater than zero", r.data)
        r = self.client.post(
            "/add",
            data={"title": "Tea", "amount": "20", "category": "Food", "spent_on": TODAY},
            follow_redirects=True,
        )
        self.assertIn(b"Expense added.", r.data)
        self.assertIn(b"Tea", r.data)


if __name__ == "__main__":
    unittest.main()
