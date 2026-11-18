"""Usage: python -m scripts.preview_chunks owner/repo pr_number"""

import sys

from dotenv import load_dotenv

from app.diff_parser import parse_diff
from app.github_client import (
    fetch_pr_diff,
    get_installation_id,
    get_installation_token,
)

load_dotenv()

if len(sys.argv) != 3:
    sys.exit("Usage: python -m scripts.preview_chunks owner/repo pr_number")

owner, repo = sys.argv[1].split("/")
pr_number = int(sys.argv[2])

token = get_installation_token(get_installation_id(owner, repo))
chunks = parse_diff(fetch_pr_diff(owner, repo, pr_number, token))

print(f"{len(chunks)} chunk(s)\n")
for i, chunk in enumerate(chunks, 1):
    print(f"--- Chunk {i}: {chunk.filename} ({len(chunk.text)} chars) ---")
    print(chunk.text[:600])
    print()