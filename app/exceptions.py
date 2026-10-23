"""Custom exceptions so the UI can show clear messages."""


class ExpenseError(Exception):
    """Base class for all expense-related errors."""


class ValidationError(ExpenseError):
    """Raised when user input is invalid."""


class InvalidAmountError(ValidationError):
    pass


class InvalidDateError(ValidationError):
    pass


class InvalidCategoryError(ValidationError):
    pass


class ExpenseNotFoundError(ExpenseError):
    pass
