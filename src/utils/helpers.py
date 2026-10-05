"""Shared utility functions and path resolution helpers."""

import os
from pathlib import Path


def get_project_root() -> Path:
    """Return the absolute path to the project root directory.

    Returns:
        Path: Project root directory path.
    """
    return Path(__file__).resolve().parent.parent.parent


def get_model_path() -> str:
    """Resolve the default serialized model artifact path.

    Checks the MODEL_PATH environment variable first, falling back
    to the relative models/best_model.pkl path within the project root.

    Returns:
        str: Absolute or relative file path to the trained model artifact.
    """
    env_path = os.environ.get("MODEL_PATH", "models/best_model.pkl")
    root_resolved = get_project_root() / env_path
    if root_resolved.exists():
        return str(root_resolved)
    return env_path


def format_price(price: float, currency: str = "EUR") -> str:
    """Format numeric price value into a formatted currency string.

    Args:
        price: Raw numeric price.
        currency: ISO 4217 currency code (e.g., 'EUR', 'USD', 'INR').

    Returns:
        str: Formatted price string with symbol.
    """
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "INR": "₹",
        "GBP": "£",
    }
    symbol = currency_symbols.get(currency.upper(), f"{currency} ")
    return f"{symbol}{price:,.2f}"
