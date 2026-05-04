"""
Username Generator — random, word combos, pattern templates, and mixed generation.
Includes smart dedup to never check the same username twice.
"""

import random
import requests
from typing import Iterator, List, Optional, Set


# ── Word Combo Lists ──
_ADJECTIVES = [
    'fast', 'cool', 'cyber', 'pixel', 'quantum', 'dark', 'neon', 'ultra', 'mega', 'hyper',
    'wild', 'epic', 'pro', 'alpha', 'omega', 'prime', 'royal', 'cosmic', 'lunar', 'solar',
    'fire', 'ice', 'storm', 'swift', 'zen', 'nova', 'vibe', 'ghost', 'shadow', 'steel',
    'crypto', 'turbo', 'nano', 'micro', 'macro', 'deep', 'bright', 'bold', 'calm', 'raw',
    'elite', 'max', 'top', 'real', 'true', 'live', 'pure', 'rare', 'bold', 'sick',
    'mad', 'lit', 'dope', 'fresh', 'clean', 'sharp', 'quick', 'smart', 'witty', 'keen',
]

_NOUNS = [
    'coder', 'ninja', 'dragon', 'phoenix', 'wolf', 'hawk', 'tiger', 'lion', 'bear', 'eagle',
    'shark', 'fox', 'cat', 'bot', 'dev', 'geek', 'hacker', 'maker', 'builder', 'runner',
    'rider', 'surfer', 'player', 'gamer', 'star', 'moon', 'sun', 'sky', 'ocean', 'wave',
    'storm', 'blade', 'shield', 'crown', 'king', 'queen', 'lord', 'master', 'chief', 'boss',
    'ace', 'hero', 'sage', 'mage', 'knight', 'monk', 'saint', 'angel', 'demon', 'ghost',
    'pixel', 'byte', 'node', 'core', 'flux', 'spark', 'glitch', 'cipher', 'signal', 'pulse',
]

# ── Pattern Symbol Map ──
_PATTERN_MAP = {
    '?': 'abcdefghijklmnopqrstuvwxyz',
    '#': '0123456789',
    '!': 'abcdefghijklmnopqrstuvwxyz0123456789',
}


class UsernameGenerator:
    """Generates or loads usernames to check with multiple strategies."""

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

        # Smart dedup
        self._seen: Set[str] = set()

    def _is_valid(self, username: str) -> bool:
        """Check if username passes all filters."""
        if len(username) < 5 or len(username) > 32:
            return False
        if not username[0].isalpha():
            return False
        if '__' in username:
            return False
        if username.endswith('_'):
            return False
        return all(f(username) for f in self.filters)

    def _is_unique(self, username: str) -> bool:
        """Check if username hasn't been generated before."""
        if username in self._seen:
            return False
        self._seen.add(username)
        return True

    @property
    def seen_count(self) -> int:
        return len(self._seen)

    def clear_seen(self):
        self._seen.clear()

    def random_stream(self) -> Iterator[str]:
        """Yield random usernames indefinitely."""
        while True:
            username = "".join(random.choice(self.chars) for _ in range(self.length))
            if self._is_valid(username) and self._is_unique(username):
                yield username

    def word_combo_stream(self) -> Iterator[str]:
        """Yield word combo usernames (adjective + noun + number)."""
        while True:
            adj = random.choice(_ADJECTIVES)
            noun = random.choice(_NOUNS)
            num = random.randint(1, 999) if random.random() > 0.4 else ''
            username = f"{adj}{noun}{num}"
            if self._is_valid(username) and self._is_unique(username):
                yield username

    def mixed_stream(self) -> Iterator[str]:
        """Yield usernames by alternating between random and word combo."""
        random_gen = self.random_stream()
        combo_gen = self.word_combo_stream()
        while True:
            if random.random() > 0.5:
                yield next(random_gen)
            else:
                yield next(combo_gen)

    def pattern_stream(self, pattern: str) -> Iterator[str]:
        """Yield usernames generated from a pattern template."""
        while True:
            username = ""
            for ch in pattern:
                if ch in _PATTERN_MAP:
                    username += random.choice(_PATTERN_MAP[ch])
                else:
                    username += ch
            if self._is_valid(username) and self._is_unique(username):
                yield username

    @staticmethod
    def validate_pattern(pattern: str) -> Optional[str]:
        """Validate a pattern template. Returns error message or None."""
        if not pattern:
            return "Pattern cannot be empty"
        if len(pattern) < 5:
            return f"Pattern too short (min 5 chars, got {len(pattern)})"
        if len(pattern) > 32:
            return f"Pattern too long (max 32 chars, got {len(pattern)})"
        if not pattern[0].isalpha() and pattern[0] not in _PATTERN_MAP:
            return "Pattern must start with a letter or ?/! placeholder"
        return None

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
