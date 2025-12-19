"""
Game module that uses random number generation.
"""

import random  # This imports the local random.py, not the standard library!
from utils import clean_text


class Game:
    """Simple number guessing game."""

    def __init__(self):
        self.score = 0
        self.rounds_played = 0

    def generate_target(self, min_val=1, max_val=100):
        """Generate a random target number."""
        return random.randint(min_val, max_val)

    def make_guess(self, target, guess):
        """Make a guess and return feedback."""
        self.rounds_played += 1

        if guess == target:
            self.score += 10
            return "correct"
        elif guess < target:
            return "too_low"
        else:
            return "too_high"

    def choose_difficulty(self):
        """Choose a random difficulty level."""
        difficulties = ["easy", "medium", "hard", "expert"]
        return random.choice(difficulties)

    def get_stats(self):
        """Get game statistics."""
        return {
            "score": self.score,
            "rounds_played": self.rounds_played,
            "average": self.score / max(self.rounds_played, 1)
        }


class TeamGame:
    """Team-based game with player shuffling."""

    def __init__(self):
        self.teams = []
        self.players = []

    def add_player(self, player_name):
        """Add a player to the game."""
        cleaned_name = clean_text(player_name)
        self.players.append(cleaned_name)

    def create_teams(self, team_size=2):
        """Create random teams from players."""
        if len(self.players) < team_size:
            raise ValueError("Not enough players for team size")

        # Shuffle players - THIS WILL FAIL!
        # The local random.py doesn't have shuffle() function
        shuffled_players = self.players.copy()
        random.shuffle(shuffled_players)  # AttributeError: module 'random' has no attribute 'shuffle'

        # Create teams
        self.teams = []
        for i in range(0, len(shuffled_players), team_size):
            team = shuffled_players[i:i + team_size]
            if len(team) == team_size:
                self.teams.append(team)

        return self.teams

    def get_team_count(self):
        """Get number of teams."""
        return len(self.teams)
