def is_score(value):
    """True for a number from 0 to 10. A bool is not a score."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 10
