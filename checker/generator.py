"""
Username Generator — random generation and wordlist loading.
"""

import random
import requests
from typing import Iterator, List, Optional


class UsernameGenerator:
    """Generates or loads usernames to check."""

    def __init__(
        self,
        length: int = 5,
        chars: str = "1234567890qwertyuiopasdfghjklzxcvbnm._",
        avoid_start_dot: bool = True,
        avoid_end_dot: bool = True,
        avoid_start_underscore: bool = False,
        avoid_end_underscore: bool = False,
        avoid_start_number: bool = False,
    ):
        self.length = length
        self.chars = chars
        self.filters = []
        if avoid_start_dot:
            self.filters.append(lambda u: u[0] != ".")
        if avoid_end_dot:
            self.filters.append(lambda u: u[-1] != ".")
        if avoid_start_underscore:
            self.filters.append(lambda u: u[0] != "_")
        if avoid_end_underscore:
            self.filters.append(lambda u: u[-1] != "_")
        if avoid_start_number:
            self.filters.append(lambda u: not u[0].isdigit())

    def _is_valid(self, username: str) -> bool:
        """Check if username passes all filters."""
        return all(f(username) for f in self.filters)

    def random_stream(self) -> Iterator[str]:
        """Yield random usernames indefinitely."""
        while True:
            username = "".join(random.choice(self.chars) for _ in range(self.length))
            if self._is_valid(username):
                yield username

    @staticmethod
    def load_from_file(path: str) -> List[str]:
        """Load usernames from a local file (one per line)."""
        try:
            with open(path, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"[!] Failed to load wordlist from {path}: {e}")
            return []

    @staticmethod
    def load_from_url(url: str) -> List[str]:
        """Load usernames from a remote URL (one per line)."""
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return [line.strip() for line in resp.text.splitlines() if line.strip()]
        except Exception as e:
            print(f"[!] Failed to load wordlist from URL: {e}")
            return []
