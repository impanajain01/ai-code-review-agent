import hashlib
import hmac
import os

import requests
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

payload = b'{"action": "opened", "pull_request": {"number": 42}, "repository": {"full_name": "test/repo"}}'

signature = "sha256=" + hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()

response = requests.post(
    "http://127.0.0.1:8000/webhook",
    data=payload,
    headers={
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json",
    },
)

print(response.status_code)
print(response.json())