"""
Custom random module - THIS SHADOWS THE STANDARD LIBRARY!
This is a simplified random module that doesn't have all the functions
of the standard library random module.
"""


class Random:
    """Simple random number generator (NOT cryptographically secure)."""

    def __init__(self, seed=None):
        self.seed = seed or 42
        self._state = self.seed

    def _next(self):
        """Generate next random number using simple LCG."""
        # Simple Linear Congruential Generator
        a = 1103515245
        c = 12345
        m = 2**31
        self._state = (a * self._state + c) % m
        return self._state

    def random_int(self, min_val, max_val):
        """Generate random integer between min_val and max_val."""
        value = self._next()
        range_size = max_val - min_val + 1
        return min_val + (value % range_size)

    def random_choice(self, items):
        """Choose random item from list."""
        if not items:
            raise ValueError("Cannot choose from empty list")
        index = self.random_int(0, len(items) - 1)
        return items[index]


# Create a default instance
_default_random = Random()


def randint(min_val, max_val):
    """Generate random integer."""
    return _default_random.random_int(min_val, max_val)


def choice(items):
    """Choose random item."""
    return _default_random.random_choice(items)


# Note: This module does NOT have shuffle() function
# which the standard library random module has
