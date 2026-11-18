"""Usage: python -m scripts.review_pr owner/repo pr_number"""

import logging
import sys

from dotenv import load_dotenv

from app.diff_parser import parse_diff
from app.github_client import (
    fetch_pr_diff,
    get_installation_id,
    get_installation_token,
)
from app.reviewer import review_chunks

load_dotenv()
logging.basicConfig(level=logging.INFO)

if len(sys.argv) != 3:
    sys.exit("Usage: python -m scripts.review_pr owner/repo pr_number")

owner, repo = sys.argv[1].split("/")
pr_number = int(sys.argv[2])

token = get_installation_token(get_installation_id(owner, repo))
chunks = parse_diff(fetch_pr_diff(owner, repo, pr_number, token))
print(f"Reviewing {len(chunks)} chunk(s)...\n")

findings = review_chunks(chunks)

if not findings:
    print("No issues found.")
for item in findings:
    f = item.finding
    print(f"[{f.severity.value.upper()}] {item.filename}:{f.line}  ({f.category.value})")
    print(f"  {f.title}")
    print(f"  {f.explanation}")
    if f.suggestion:
        print(f"  Fix: {f.suggestion}")
    print()