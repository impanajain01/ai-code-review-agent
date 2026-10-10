"""
AI Code Review Agent - main application entrypoint.
"""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.webhooks import router as webhook_router

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Code Review Agent",
    description="An agent that automatically reviews GitHub pull requests using an LLM.",
    version="0.1.0",
)

app.include_router(webhook_router)


@app.get("/")
def root():
    """Simple root endpoint so visiting the base URL doesn't 404."""
    return {"message": "AI Code Review Agent is running"}


@app.get("/health")
def health_check():
    """Health check endpoint - used to verify the service is up."""
    return {"status": "ok"}