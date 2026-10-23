"""Data model."""
from dataclasses import dataclass


@dataclass
class Expense:
    id: int
    title: str
    amount: float
    category: str
    spent_on: str  # YYYY-MM-DD
    note: str = ""

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            title=row["title"],
            amount=row["amount"],
            category=row["category"],
            spent_on=row["spent_on"],
            note=row["note"] or "",
        )
