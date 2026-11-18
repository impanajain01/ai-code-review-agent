"""
LLM-based reviewer: sends diff chunks to Gemini and returns structured findings.

The model is forced to answer in JSON matching the ReviewResult schema, so
we get typed data back (file, line, severity, ...) instead of free text.
"""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from app.diff_parser import DiffChunk

logger = logging.getLogger("reviewer")

DEFAULT_MODEL = "gemini-2.5-flash"  # override with GEMINI_MODEL in .env
MAX_RETRIES = 3
RETRYABLE_CODES = {429, 500, 503}  # rate limit / temporary server trouble

SYSTEM_PROMPT = """You are a senior software engineer doing a pull request review.

You receive part of a diff for ONE file. Each line starts with its line number
in the NEW version of the file, then a marker: '+' added, '-' removed,
blank = unchanged context.

Rules:
- Only report issues on ADDED lines ('+'). Use the line number from the left column.
- Look for: real bugs, security vulnerabilities (injection, hardcoded secrets,
  unsafe deserialization, missing auth checks), performance problems, and
  serious maintainability issues.
- Do NOT nitpick formatting, naming taste, or missing docstrings.
- Only report issues you are confident about. Quality beats quantity.
- If the code looks fine, return an empty findings list.
- Keep explanations short and concrete, and give a specific fix when you can."""


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Category(str, Enum):
    bug = "bug"
    security = "security"
    performance = "performance"
    maintainability = "maintainability"


class Finding(BaseModel):
    line: int = Field(description="Line number in the NEW file, from the left column. Must be an added line.")
    severity: Severity
    category: Category
    title: str = Field(description="Short summary, under 10 words")
    explanation: str = Field(description="Why this is a problem, 1-3 sentences")
    suggestion: str = Field(description="Concrete fix. Empty string if none.")


class ReviewResult(BaseModel):
    findings: list[Finding]


@dataclass
class ReviewedFinding:
    filename: str
    finding: Finding


def _call_model(chunk: DiffChunk) -> ReviewResult:
    """Send one chunk to Gemini and return the parsed result (with retries)."""
    # Created per call (not at import time) so .env is always loaded first.
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    prompt = f"File: {chunk.filename}\n\n{chunk.text}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ReviewResult,
                    temperature=0.2,  # low = more consistent reviews
                ),
            )
            if isinstance(response.parsed, ReviewResult):
                return response.parsed
            return ReviewResult.model_validate_json(response.text)

        except errors.APIError as exc:
            if exc.code in RETRYABLE_CODES and attempt < MAX_RETRIES:
                wait = 5 * 2 ** (attempt - 1)  # 5s, then 10s
                logger.warning("Gemini error %s, retrying in %ss", exc.code, wait)
                time.sleep(wait)
                continue
            raise

    raise RuntimeError("unreachable")


def review_chunks(chunks: list[DiffChunk]) -> list[ReviewedFinding]:
    """Review every chunk. One failed chunk must not sink the whole review."""
    reviewed: list[ReviewedFinding] = []
    for chunk in chunks:
        try:
            result = _call_model(chunk)
        except Exception:
            logger.exception("Review failed for %s, skipping this chunk", chunk.filename)
            continue
        reviewed.extend(ReviewedFinding(chunk.filename, f) for f in result.findings)
    return reviewed