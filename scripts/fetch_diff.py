"""Usage (from project root): python -m scripts.fetch_diff owner/repo pr_number"""

import sys

from dotenv import load_dotenv

from app.github_client import (
    fetch_pr_diff,
    get_installation_id,
    get_installation_token,
)

load_dotenv()

if len(sys.argv) != 3:
    sys.exit("Usage: python -m scripts.fetch_diff owner/repo pr_number")

owner, repo = sys.argv[1].split("/")
pr_number = int(sys.argv[2])

installation_id = get_installation_id(owner, repo)
token = get_installation_token(installation_id)
diff = fetch_pr_diff(owner, repo, pr_number, token)

print(f"Fetched diff: {len(diff)} characters\n")
print(diff[:2000])