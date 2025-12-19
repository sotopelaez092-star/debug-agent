"""
Main application that demonstrates module shadowing issue.
The local random.py shadows the standard library random module,
causing AttributeError when trying to use functions that don't exist in the local module.
"""

from game import Game, TeamGame
from data_processor import DataProcessor
from simulator import Simulator


def test_basic_game():
    """Test basic game functionality - this works."""
    print("=== Testing Basic Game ===")
    game = Game()
    target = game.generate_target(1, 10)
    print(f"Generated target: {target}")

    result = game.make_guess(target, 5)
    print(f"Guess result: {result}")

    difficulty = game.choose_difficulty()
    print(f"Random difficulty: {difficulty}")

    stats = game.get_stats()
    print(f"Game stats: {stats}\n")


def test_team_game():
    """Test team game - THIS WILL FAIL."""
    print("=== Testing Team Game ===")
    team_game = TeamGame()

    # Add players
    team_game.add_player("Alice")
    team_game.add_player("Bob")
    team_game.add_player("Charlie")
    team_game.add_player("Diana")

    # This will fail because random.shuffle() doesn't exist in local random.py
    try:
        teams = team_game.create_teams(team_size=2)
        print(f"Created teams: {teams}")
    except AttributeError as e:
        print(f"ERROR: {e}")
        raise


def test_data_processor():
    """Test data processor - THIS WILL FAIL."""
    print("=== Testing Data Processor ===")
    processor = DataProcessor()
    processor.add_data([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # This will fail because random.sample() doesn't exist in local random.py
    try:
        sample = processor.sample_data(3)
        print(f"Random sample: {sample}")
    except AttributeError as e:
        print(f"ERROR: {e}")


def test_simulator():
    """Test simulator - THIS WILL FAIL."""
    print("=== Testing Simulator ===")
    # This will fail because random.seed() doesn't exist in local random.py
    try:
        sim = Simulator(seed=42)
        result = sim.run_simulation("test_event", iterations=5)
        print(f"Simulation result: {result}")
    except AttributeError as e:
        print(f"ERROR: {e}")


def main():
    """Main function."""
    print("=== Module Shadowing Demo ===\n")

    # Test basic functionality that works
    test_basic_game()

    # Test team game that fails
    test_team_game()


if __name__ == "__main__":
    main()
