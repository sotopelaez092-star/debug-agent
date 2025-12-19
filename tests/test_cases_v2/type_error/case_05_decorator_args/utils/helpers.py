"""Utility helper functions with caching."""
from decorators import cache
import time
import hashlib


@cache  # BUG: Old decorator syntax without TTL
def compute_hash(data):
    """
    Compute MD5 hash of data (cached for performance).

    Uses old @cache decorator syntax.
    """
    print(f"  [COMPUTE] Computing hash for data...")
    time.sleep(0.05)

    if isinstance(data, str):
        data = data.encode()
    elif not isinstance(data, bytes):
        data = str(data).encode()

    return hashlib.md5(data).hexdigest()


@cache  # BUG: Old syntax
def fibonacci(n):
    """
    Calculate fibonacci number (expensive for large n).

    Classic example of where caching is beneficial.
    """
    print(f"  [COMPUTE] Computing fibonacci({n})...")

    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@cache  # BUG: Old syntax
def factorial(n):
    """Calculate factorial (cached)."""
    print(f"  [COMPUTE] Computing factorial({n})...")

    if n <= 1:
        return 1
    return n * factorial(n - 1)


@cache  # BUG: Old syntax
def is_prime(n):
    """Check if number is prime (cached)."""
    print(f"  [COMPUTE] Checking if {n} is prime...")
    time.sleep(0.05)

    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False

    return True


def validate_input(value, min_val=None, max_val=None):
    """Validate input value (not cached)."""
    if min_val is not None and value < min_val:
        raise ValueError(f"Value {value} is less than minimum {min_val}")
    if max_val is not None and value > max_val:
        raise ValueError(f"Value {value} is greater than maximum {max_val}")
    return True
