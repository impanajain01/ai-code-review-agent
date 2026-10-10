"""
Webhook receiver for GitHub pull request events.

GitHub signs every webhook payload with HMAC-SHA256 using the secret
we configured in the GitHub App settings. We verify that signature here
so we only ever act on requests that genuinely came from GitHub -
this prevents anyone else from spoofing a webhook call to our service.
"""

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request

logger = logging.getLogger("webhooks")

router = APIRouter()


def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """
    Verify that the payload was signed by GitHub using our webhook secret.

    GitHub sends the signature in the 'X-Hub-Signature-256' header as
    'sha256=<hex digest>'. We recompute the digest ourselves using the
    same secret and compare - if they don't match, the request is either
    forged or corrupted, and we reject it.
    """
    if not signature_header:
        return False

    # Read the secret at request time (not import time) so it's always
    # loaded from .env by the time we need it.
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        # Fail closed: reject rather than silently accepting unverified requests.
        logger.warning("GITHUB_WEBHOOK_SECRET is not set - rejecting request")
        return False

    expected_signature = "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # compare_digest prevents timing attacks that a plain '==' would allow.
    return hmac.compare_digest(expected_signature, signature_header)


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    """
    Receive and process GitHub webhook events.

    For Day 2, we only verify the signature and log what event came in.
    Diff fetching and review logic get added in the following days.
    """
    raw_body = await request.body()

    if not verify_signature(raw_body, x_hub_signature_256):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    logger.info(f"Received verified GitHub event: {x_github_event}")

    if x_github_event == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("pull_request", {}).get("number")
        repo_name = payload.get("repository", {}).get("full_name")

        logger.info(
            f"Pull request event: action={action}, "
            f"repo={repo_name}, pr_number={pr_number}"
        )

        if action in ("opened", "synchronize"):
            # This is where Day 3+ will kick off the diff fetch and review.
            logger.info(f"PR #{pr_number} on {repo_name} triggered for review")

    return {"status": "received"}