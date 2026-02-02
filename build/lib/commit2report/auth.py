"""GitHub authentication module."""

import logging
import os

from dotenv import load_dotenv
from github import Github, GithubException

# Configure logging
logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when GitHub authentication fails."""

    pass


def get_github_client() -> Github:
    """
    Create and return a GitHub client.

    Reads the GITHUB_TOKEN from environment variables or .env file.
    If no token is provided, creates an unauthenticated client that can
    access public repositories (with lower rate limits).

    Returns:
        Github: GitHub client instance (authenticated or unauthenticated).

    Raises:
        AuthenticationError: If authentication with the provided token fails.
    """
    # Load .env file if present
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        # Return unauthenticated client for public repositories
        # Note: Rate limit is 60 requests/hour for unauthenticated clients
        logger.warning(
            "GITHUB_TOKEN is not set. "
            "Only public repositories can be accessed (rate limit: 60 req/hour). "
            "For private repositories, set GITHUB_TOKEN environment variable."
        )
        return Github()

    try:
        client = Github(token)
        # Verify authentication by making a simple API call
        client.get_user().login
        return client
    except GithubException as e:
        if e.status == 401:
            raise AuthenticationError(
                "GitHub authentication failed: Invalid or expired token.\n"
                "Please check your GITHUB_TOKEN and try again."
            )
        raise AuthenticationError(f"GitHub authentication failed: {e}")
