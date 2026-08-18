"""
AI Code Review Agent - main application entrypoint.

Day 1: bare FastAPI skeleton with a health check endpoint.
We'll build out the webhook receiver, diff fetcher, and LLM review
logic in the days that follow.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Code Review Agent",
    description="An agent that automatically reviews GitHub pull requests using an LLM.",
    version="0.1.0",
)


@app.get("/")
def root():
    """Simple root endpoint so visiting the base URL doesn't 404."""
    return {"message": "AI Code Review Agent is running"}


@app.get("/health")
def health_check():
    """Health check endpoint - used to verify the service is up."""
    return {"status": "ok"}