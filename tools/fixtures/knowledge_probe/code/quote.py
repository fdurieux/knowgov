# knowgov-keys: quote|currency, rate|rounding
"""The knowledge probe's synthetic code file (task-0360): its header cites two keys."""


def price(amount: float) -> str:
    return f"EUR {round(amount, 2):.2f}"
