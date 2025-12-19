"""
Simulation utilities using random numbers.
"""

import random
from utils import capitalize_words


class Simulator:
    """Run simulations with random events."""

    def __init__(self, seed=None):
        if seed:
            # Try to seed the random module - THIS WILL FAIL!
            # The local random.py doesn't have seed() function
            random.seed(seed)
        self.events = []

    def simulate_event(self, event_name):
        """Simulate a random event."""
        probability = random.randint(1, 100)
        success = probability > 50

        event = {
            "name": capitalize_words(event_name),
            "probability": probability,
            "success": success
        }
        self.events.append(event)
        return event

    def run_simulation(self, event_name, iterations=10):
        """Run multiple iterations of simulation."""
        results = []
        for i in range(iterations):
            event = self.simulate_event(f"{event_name} {i+1}")
            results.append(event)

        return {
            "total_runs": iterations,
            "successes": sum(1 for e in results if e["success"]),
            "failures": sum(1 for e in results if not e["success"]),
            "results": results
        }
