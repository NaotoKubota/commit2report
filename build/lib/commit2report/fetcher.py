"""GitHub commit data fetcher module."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from github import Github, GithubException

from .parser import CommitInfo


class FetchError(Exception):
    """Raised when fetching commit data fails."""

    pass


@dataclass
class FileChange:
    """Information about a changed file in a commit."""

    filename: str
    status: str  # 'added', 'modified', 'removed', 'renamed'
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]  # May be None for binary files or large diffs
    previous_filename: Optional[str] = None  # For renamed files


@dataclass
class CommitData:
    """Complete commit data fetched from GitHub API."""

    # Basic info
    sha: str
    short_sha: str
    url: str
    html_url: str

    # Repository info
    owner: str
    repo: str
    full_repo_name: str

    # Commit metadata
    message: str
    author_name: str
    author_email: str
    author_date: datetime
    committer_name: str
    committer_email: str
    committer_date: datetime

    # Statistics
    total_additions: int
    total_deletions: int
    total_changes: int
    files_changed: int

    # Changed files
    files: List[FileChange] = field(default_factory=list)


def fetch_commit(client: Github, commit_info: CommitInfo) -> CommitData:
    """
    Fetch complete commit data from GitHub API.

    Args:
        client: Authenticated GitHub client.
        commit_info: Parsed commit URL information.

    Returns:
        CommitData: Complete commit data.

    Raises:
        FetchError: If fetching the commit fails.
    """
    try:
        repo = client.get_repo(commit_info.full_repo_name)
    except GithubException as e:
        if e.status == 404:
            raise FetchError(
                f"Repository not found: {commit_info.full_repo_name}\n"
                "Please check the repository name and your access permissions."
            )
        elif e.status == 401:
            raise FetchError(
                f"Unauthorized access to repository: {commit_info.full_repo_name}\n"
                "Please check your GitHub token permissions."
            )
        elif e.status == 403:
            if "rate limit" in str(e).lower():
                raise FetchError(
                    "GitHub API rate limit exceeded.\n"
                    "Please wait a while and try again."
                )
            raise FetchError(
                f"Access forbidden to repository: {commit_info.full_repo_name}\n"
                "Please check your GitHub token permissions."
            )
        raise FetchError(f"Failed to access repository: {e}")

    try:
        commit = repo.get_commit(commit_info.sha)
    except GithubException as e:
        if e.status == 404:
            raise FetchError(
                f"Commit not found: {commit_info.sha}\n"
                f"Repository: {commit_info.full_repo_name}"
            )
        raise FetchError(f"Failed to fetch commit: {e}")

    # Extract file changes
    files = []
    for file in commit.files:
        file_change = FileChange(
            filename=file.filename,
            status=file.status,
            additions=file.additions,
            deletions=file.deletions,
            changes=file.changes,
            patch=file.patch,
            previous_filename=file.previous_filename,
        )
        files.append(file_change)

    # Build commit data
    commit_data = CommitData(
        sha=commit.sha,
        short_sha=commit.sha[:7],
        url=commit_info.url,
        html_url=commit.html_url,
        owner=commit_info.owner,
        repo=commit_info.repo,
        full_repo_name=commit_info.full_repo_name,
        message=commit.commit.message,
        author_name=commit.commit.author.name,
        author_email=commit.commit.author.email,
        author_date=commit.commit.author.date,
        committer_name=commit.commit.committer.name,
        committer_email=commit.commit.committer.email,
        committer_date=commit.commit.committer.date,
        total_additions=commit.stats.additions,
        total_deletions=commit.stats.deletions,
        total_changes=commit.stats.total,
        files_changed=len(files),
        files=files,
    )

    return commit_data


def fetch_commits(client: Github, commit_infos: List[CommitInfo]) -> List[CommitData]:
    """
    Fetch multiple commits from GitHub API.

    Args:
        client: Authenticated GitHub client.
        commit_infos: List of parsed commit URL information.

    Returns:
        List[CommitData]: List of complete commit data.

    Raises:
        FetchError: If fetching any commit fails (fails fast).
    """
    commits = []
    for commit_info in commit_infos:
        commit_data = fetch_commit(client, commit_info)
        commits.append(commit_data)
    return commits
