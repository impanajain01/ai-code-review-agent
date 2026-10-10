"""
GitHub API client: authenticates as our GitHub App and fetches PR diffs.

Auth flow:
  1. Sign a short-lived JWT with the app's private key (proves we are the app).
  2. Exchange the JWT for an installation access token (grants repo access).
  3. Use the installation token for regular API calls.
"""

import os
import time

import jwt
import requests

GITHUB_API = "https://api.github.com"
TIMEOUT = 15  # seconds; never let a network call hang forever


def _headers(token: str, accept: str = "application/vnd.github+json") -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_app_jwt() -> str:
    """Create a JWT that identifies our GitHub App (valid for ~9 minutes)."""
    app_id = os.environ["GITHUB_APP_ID"]
    key_path = os.environ["GITHUB_PRIVATE_KEY_PATH"]

    with open(key_path, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,   # backdated 60s to allow for clock drift
        "exp": now + 540,  # GitHub allows a maximum of 10 minutes
        "iss": str(app_id),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_id(owner: str, repo: str) -> int:
    """Look up the installation ID of our app on a given repo."""
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/installation",
        headers=_headers(create_app_jwt()),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["id"]


def get_installation_token(installation_id: int) -> str:
    """Exchange our app JWT for a token that can access the installed repo."""
    response = requests.post(
        f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
        headers=_headers(create_app_jwt()),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["token"]


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the raw unified diff for a pull request."""
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=_headers(token, accept="application/vnd.github.v3.diff"),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.text