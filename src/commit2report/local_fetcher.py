"""Local Git repository commit data fetcher module."""

import os
from typing import Optional

from git import InvalidGitRepositoryError, Repo
from git.exc import BadName

from .fetcher import CommitData, FileChange


class LocalFetchError(Exception):
    """Raised when fetching local commit data fails."""

    pass


def fetch_local_commit(repo_path: str, ref: str) -> CommitData:
    """
    Fetch complete commit data from a local Git repository.

    Args:
        repo_path: Path to the local Git repository.
        ref: Commit reference (SHA, branch name, tag, HEAD, etc.).

    Returns:
        CommitData: Complete commit data.

    Raises:
        LocalFetchError: If fetching the commit fails.
    """
    # Validate and open repository
    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        raise LocalFetchError(
            f"Not a valid Git repository: {repo_path}\n"
            "Please specify a valid Git repository path."
        )
    except Exception as e:
        raise LocalFetchError(f"Failed to open repository: {e}")

    # Resolve the commit reference
    try:
        commit = repo.commit(ref)
    except BadName:
        raise LocalFetchError(
            f"Commit reference not found: {ref}\n"
            "Please specify a valid commit SHA, branch name, or tag."
        )
    except Exception as e:
        raise LocalFetchError(f"Failed to resolve commit reference: {e}")

    # Extract repository name from path
    repo_name = os.path.basename(os.path.abspath(repo_path))

    # Get diff with parent commit
    files = []
    if commit.parents:
        # Normal commit with parent
        parent = commit.parents[0]
        diffs = parent.diff(commit, create_patch=True)
    else:
        # Initial commit (no parent)
        diffs = commit.diff(None, create_patch=True)

    for diff in diffs:
        # Determine file status
        if diff.new_file:
            status = "added"
            filename = diff.b_path
            previous_filename = None
        elif diff.deleted_file:
            status = "removed"
            filename = diff.a_path
            previous_filename = None
        elif diff.renamed:
            status = "renamed"
            filename = diff.b_path
            previous_filename = diff.a_path
        else:
            status = "modified"
            filename = diff.b_path or diff.a_path
            previous_filename = None

        # Get patch content
        try:
            patch = diff.diff.decode("utf-8", errors="replace") if diff.diff else None
        except Exception:
            patch = None

        # Calculate line statistics from patch
        additions, deletions = _count_lines_from_patch(patch)

        file_change = FileChange(
            filename=filename,
            status=status,
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            patch=patch,
            previous_filename=previous_filename,
        )
        files.append(file_change)

    # Calculate totals
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)
    total_changes = total_additions + total_deletions

    # Build CommitData
    return CommitData(
        sha=commit.hexsha,
        short_sha=commit.hexsha[:7],
        url="",  # Local commit, no URL
        html_url="",  # Local commit, no URL
        owner="",  # Local commit
        repo=repo_name,
        full_repo_name=repo_name,
        message=commit.message.strip(),
        author_name=commit.author.name or "",
        author_email=commit.author.email or "",
        author_date=commit.authored_datetime,
        committer_name=commit.committer.name or "",
        committer_email=commit.committer.email or "",
        committer_date=commit.committed_datetime,
        total_additions=total_additions,
        total_deletions=total_deletions,
        total_changes=total_changes,
        files_changed=len(files),
        files=files,
    )


def _count_lines_from_patch(patch: Optional[str]) -> tuple:
    """
    Count additions and deletions from a patch string.

    Args:
        patch: The diff patch content.

    Returns:
        Tuple of (additions, deletions).
    """
    if not patch:
        return 0, 0

    additions = 0
    deletions = 0

    for line in patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return additions, deletions
