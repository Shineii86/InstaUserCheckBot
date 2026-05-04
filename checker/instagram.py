"""
Instagram API Client — session management, CSRF, username availability check.
Handles rate limiting, retries, User-Agent rotation, and exponential backoff.
"""

import random
import time
import requests
from typing import Optional, Tuple
from .proxy import ProxyManager


# Result constants
AVAILABLE = "available"
TAKEN = "taken"
RATE_LIMITED = "rate_limited"
ERROR = "error"


class InstagramClient:
    """Checks Instagram username availability via the signup AJAX endpoint."""

    SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
    CHECK_URL = "https://www.instagram.com/accounts/web_create_ajax/attempt/"
    APP_ID = "936619743392459"

    def __init__(self, user_agents: list, proxy_manager: Optional[ProxyManager] = None,
                 max_retries: int = 3, retry_backoff_base: float = 2.0):
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.proxy_mgr = proxy_manager
        self._session = requests.Session()
        self._csrf_token: Optional[str] = None
        self._token_fetched_at: float = 0
        self._token_ttl: float = 300  # refresh CSRF every 5 minutes

        # Retry config
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base

        # Rate limit tracking
        self._consecutive_rate_limits = 0
        self._total_rate_limits = 0

    def _get_ua(self) -> str:
        return random.choice(self.user_agents)

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        base = self.retry_backoff_base ** attempt
        jitter = random.uniform(0, base * 0.5)
        return min(base + jitter, 30.0)  # cap at 30s

    @property
    def consecutive_rate_limits(self) -> int:
        return self._consecutive_rate_limits

    @property
    def total_rate_limits(self) -> int:
        return self._total_rate_limits

    @property
    def recommended_delay(self) -> float:
        """Dynamic delay based on rate limit history."""
        if self._consecutive_rate_limits >= 5:
            return 5.0
        elif self._consecutive_rate_limits >= 3:
            return 3.0
        elif self._consecutive_rate_limits >= 1:
            return 2.0
        return 0.0

    def _refresh_csrf(self) -> bool:
        """Fetch a fresh CSRF token. Returns True on success."""
        headers = {"User-Agent": self._get_ua()}
        proxy = self.proxy_mgr.get_random() if self.proxy_mgr else None
        try:
            self._session.get(self.SIGNUP_URL, headers=headers, proxies=proxy, timeout=15)
            token = self._session.cookies.get("csrftoken")
            if token:
                self._csrf_token = token
                self._token_fetched_at = time.monotonic()
                return True
        except Exception:
            pass
        return False

    def _ensure_csrf(self) -> bool:
        """Ensure we have a valid CSRF token."""
        now = time.monotonic()
        if self._csrf_token and (now - self._token_fetched_at) < self._token_ttl:
            return True
        return self._refresh_csrf()

    def check(self, username: str, delay: float = 0.5) -> Tuple[str, str]:
        """
        Check a single username availability with retry logic.

        Returns:
            (status, username) where status is AVAILABLE, TAKEN, RATE_LIMITED, or ERROR
        """
        for attempt in range(self.max_retries + 1):
            if not self._ensure_csrf():
                if attempt < self.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                return (ERROR, username)

            headers = {
                "Host": "www.instagram.com",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self._get_ua(),
                "X-IG-App-ID": self.APP_ID,
                "X-CSRFToken": self._csrf_token,
                "Referer": self.SIGNUP_URL,
            }

            # Generate a realistic dummy email per request
            random_prefix = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
            email = f"{random_prefix}@gmail.com"

            data = {
                "email": email,
                "username": username,
                "first_name": "",
                "opt_into_one_tap": "false",
            }

            proxy = self.proxy_mgr.get_random() if self.proxy_mgr else None

            try:
                resp = self._session.post(
                    self.CHECK_URL,
                    headers=headers,
                    data=data,
                    proxies=proxy,
                    timeout=15,
                )
                text = resp.text

                if "feedback_required" in text:
                    self._consecutive_rate_limits += 1
                    self._total_rate_limits += 1
                    # Auto-refresh CSRF on rate limit
                    self._csrf_token = None
                    if attempt < self.max_retries:
                        time.sleep(self._calculate_backoff(attempt))
                        continue
                    return (RATE_LIMITED, username)
                elif "username_is_taken" in text:
                    self._consecutive_rate_limits = 0
                    return (TAKEN, username)
                else:
                    self._consecutive_rate_limits = 0
                    return (AVAILABLE, username)

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                return (ERROR, username)
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                return (ERROR, username)
            except Exception:
                if attempt < self.max_retries:
                    time.sleep(self._calculate_backoff(attempt))
                    continue
                return (ERROR, username)
            finally:
                if delay > 0 and attempt == self.max_retries:
                    time.sleep(delay)

        return (ERROR, username)
