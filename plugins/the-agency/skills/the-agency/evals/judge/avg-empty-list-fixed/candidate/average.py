def average(values):
    """Return the mean of a list of numbers. An empty list returns 0."""
    if not values:
        return 0
    return sum(values) / len(values)
