"""GitHub commit URL parser module."""

import re
from dataclasses import dataclass
from typing import List


class ParseError(Exception):
    """Raised when URL parsing fails."""

    pass


@dataclass
class CommitInfo:
    """Parsed commit URL information."""

    owner: str
    repo: str
    sha: str
    url: str

    @property
    def full_repo_name(self) -> str:
        """Return the full repository name (owner/repo)."""
        return f"{self.owner}/{self.repo}"


# Regex pattern for GitHub commit URLs
# Matches: https://github.com/{owner}/{repo}/commit/{sha}
COMMIT_URL_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/commit/([a-fA-F0-9]+)/?$"
)


def parse_commit_url(url: str) -> CommitInfo:
    """
    Parse a GitHub commit URL and extract owner, repo, and SHA.

    Args:
        url: GitHub commit URL (e.g., https://github.com/owner/repo/commit/abc123)

    Returns:
        CommitInfo: Parsed commit information.

    Raises:
        ParseError: If the URL format is invalid.
    """
    url = url.strip()

    match = COMMIT_URL_PATTERN.match(url)
    if not match:
        raise ParseError(
            f"Invalid GitHub commit URL format: {url}\n"
            "Expected format: https://github.com/owner/repo/commit/sha"
        )

    owner, repo, sha = match.groups()

    return CommitInfo(owner=owner, repo=repo, sha=sha, url=url)


def parse_commit_urls(urls: List[str]) -> List[CommitInfo]:
    """
    Parse multiple GitHub commit URLs.

    Args:
        urls: List of GitHub commit URLs.

    Returns:
        List[CommitInfo]: List of parsed commit information.

    Raises:
        ParseError: If any URL format is invalid.
    """
    if not urls:
        raise ParseError("No commit URLs provided.")

    return [parse_commit_url(url) for url in urls]


def load_urls_from_file(filepath: str) -> List[str]:
    """
    Load commit URLs from a file (one URL per line).

    Args:
        filepath: Path to the file containing URLs.

    Returns:
        List[str]: List of URLs from the file.

    Raises:
        ParseError: If the file cannot be read or is empty.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        raise ParseError(f"URL file not found: {filepath}")
    except IOError as e:
        raise ParseError(f"Failed to read URL file: {filepath}\n{e}")

    if not urls:
        raise ParseError(f"No URLs found in file: {filepath}")

    return urls
