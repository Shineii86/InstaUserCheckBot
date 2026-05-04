"""
Instagram API Client — session management, CSRF, username availability check.
Handles rate limiting, retries, and User-Agent rotation.
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

    def __init__(self, user_agents: list, proxy_manager: Optional[ProxyManager] = None):
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.proxy_mgr = proxy_manager
        self._session = requests.Session()
        self._csrf_token: Optional[str] = None
        self._token_fetched_at: float = 0
        self._token_ttl: float = 300  # refresh CSRF every 5 minutes

    def _get_ua(self) -> str:
        return random.choice(self.user_agents)

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
        Check a single username availability.

        Returns:
            (status, username) where status is AVAILABLE, TAKEN, RATE_LIMITED, or ERROR
        """
        if not self._ensure_csrf():
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
                return (RATE_LIMITED, username)
            elif "username_is_taken" in text:
                return (TAKEN, username)
            else:
                return (AVAILABLE, username)

        except requests.exceptions.Timeout:
            return (ERROR, username)
        except requests.exceptions.ConnectionError:
            return (ERROR, username)
        except Exception:
            return (ERROR, username)
        finally:
            if delay > 0:
                time.sleep(delay)
