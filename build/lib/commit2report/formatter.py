"""Report formatter module."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from .fetcher import CommitData, FileChange


@dataclass
class NotebookCellChange:
    """Represents a change in a Jupyter Notebook cell."""

    cell_type: str  # 'code' or 'markdown'
    changes: List[str]  # Changed lines (with +/- prefix)


def is_notebook_file(filename: str) -> bool:
    """Check if the file is a Jupyter Notebook."""
    return filename.endswith(".ipynb")


def parse_notebook_patch(patch: Optional[str]) -> List[NotebookCellChange]:
    """
    Parse a Jupyter Notebook patch and extract code cell changes.

    Args:
        patch: The raw patch content from GitHub API.

    Returns:
        List of NotebookCellChange objects containing code cell changes only.
    """
    if patch is None:
        return []

    cells = []
    current_cell_changes: List[str] = []
    current_cell_type: Optional[str] = None
    in_source_block = False

    # Pattern to detect cell type
    cell_type_pattern = re.compile(r'^[+-]\s*"cell_type":\s*"(code|markdown)"')
    # Pattern to detect source block start
    source_start_pattern = re.compile(r'^[+-]\s*"source":\s*\[')
    # Pattern to detect source content line
    source_line_pattern = re.compile(r'^([+-])\s*"(.*)"')

    lines = patch.split("\n")

    for line in lines:
        # Check for cell type
        cell_type_match = cell_type_pattern.match(line)
        if cell_type_match:
            # Save previous cell if exists and is code type
            if current_cell_changes and current_cell_type == "code":
                cells.append(NotebookCellChange(
                    cell_type=current_cell_type,
                    changes=current_cell_changes,
                ))
            # Start new cell
            current_cell_type = cell_type_match.group(1)
            current_cell_changes = []
            in_source_block = False
            continue

        # Check for source block start
        if source_start_pattern.match(line):
            in_source_block = True
            continue

        # Check for source block end (line with just ] or ],)
        if in_source_block and re.match(r'^[+-]?\s*\],?\s*$', line):
            in_source_block = False
            continue

        # Extract source content if in source block and it's a code cell
        if in_source_block and current_cell_type == "code":
            source_match = source_line_pattern.match(line)
            if source_match:
                prefix = source_match.group(1)
                content = source_match.group(2)
                # Unescape JSON string
                content = content.replace('\\n', '').replace('\\t', '\t')
                content = content.replace('\\"', '"')
                # Remove trailing comma if present
                content = content.rstrip(',')
                if content.endswith('"'):
                    content = content[:-1]
                if content:  # Only add non-empty lines
                    current_cell_changes.append(f"{prefix} {content}")

    # Save last cell if it's code type
    if current_cell_changes and current_cell_type == "code":
        cells.append(NotebookCellChange(
            cell_type=current_cell_type,
            changes=current_cell_changes,
        ))

    return cells


def format_notebook_changes(
    cells: List[NotebookCellChange],
    max_cells: Optional[int] = None,
) -> tuple[str, bool]:
    """
    Format Jupyter Notebook cell changes.

    Args:
        cells: List of cell changes.
        max_cells: Maximum number of cells to show.

    Returns:
        Tuple of (formatted string, was_truncated).
    """
    if not cells:
        return "(Jupyter Notebook - no code cell changes detected)", False

    lines = ["Jupyter Notebook code cell changes:"]
    was_truncated = False

    cells_to_show = cells
    if max_cells is not None and len(cells) > max_cells:
        cells_to_show = cells[:max_cells]
        was_truncated = True

    for i, cell in enumerate(cells_to_show, 1):
        lines.append("")
        lines.append(f"[Code Cell {i}]")
        for change in cell.changes:
            lines.append(f"  {change}")

    if was_truncated:
        lines.append("")
        lines.append(f"... (truncated, showing first {max_cells} of {len(cells)} cells)")

    return "\n".join(lines), was_truncated


def get_local_timezone():
    """Get the system's local timezone."""
    return datetime.now().astimezone().tzinfo


def format_datetime(dt: datetime) -> str:
    """
    Format a datetime to local timezone string.

    Args:
        dt: UTC datetime from GitHub API.

    Returns:
        Formatted datetime string in local timezone.
    """
    # GitHub API returns UTC time
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to local timezone
    local_dt = dt.astimezone(get_local_timezone())
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_status_symbol(status: str) -> str:
    """
    Get the symbol for a file change status.

    Args:
        status: File status from GitHub API.

    Returns:
        Single-letter status symbol.
    """
    status_map = {
        "added": "A",
        "modified": "M",
        "removed": "D",
        "renamed": "R",
        "copied": "C",
        "changed": "M",
    }
    return status_map.get(status.lower(), "?")


def truncate_patch(patch: Optional[str], max_lines: Optional[int]) -> tuple[str, bool]:
    """
    Truncate patch content if it exceeds max_lines.

    Args:
        patch: The patch content (may be None).
        max_lines: Maximum number of lines to keep (None for unlimited).

    Returns:
        Tuple of (truncated patch, was_truncated).
    """
    if patch is None:
        return "(binary file or diff not available)", False

    if max_lines is None:
        return patch, False

    lines = patch.split("\n")
    if len(lines) <= max_lines:
        return patch, False

    truncated = "\n".join(lines[:max_lines])
    return truncated, True


def format_file_change(
    file: FileChange,
    max_diff_lines: Optional[int] = None,
    max_notebook_cells: Optional[int] = None,
) -> str:
    """
    Format a single file change.

    Args:
        file: File change information.
        max_diff_lines: Maximum number of diff lines to show.
        max_notebook_cells: Maximum number of notebook cells to show.

    Returns:
        Formatted file change string.
    """
    lines = []
    separator = "─" * 40

    # File header with status and stats
    status_symbol = get_status_symbol(file.status)
    header = f"[{status_symbol}] {file.filename} (+{file.additions}, -{file.deletions})"

    # Add previous filename for renamed files
    if file.previous_filename:
        header += f" (from {file.previous_filename})"

    lines.append(separator)
    lines.append(header)
    lines.append(separator)

    # Check if this is a Jupyter Notebook file
    if is_notebook_file(file.filename):
        # Parse and format notebook changes
        cells = parse_notebook_patch(file.patch)
        notebook_content, _ = format_notebook_changes(cells, max_notebook_cells)
        lines.append(notebook_content)
    else:
        # Regular file - show patch content
        patch, was_truncated = truncate_patch(file.patch, max_diff_lines)
        lines.append(patch)

        if was_truncated:
            lines.append(f"... (truncated, showing first {max_diff_lines} lines)")

    return "\n".join(lines)


def format_commit(
    commit: CommitData,
    index: int,
    total: int,
    max_diff_lines: Optional[int] = None,
    max_notebook_cells: Optional[int] = None,
) -> str:
    """
    Format a single commit.

    Args:
        commit: Complete commit data.
        index: 1-based index of this commit.
        total: Total number of commits.
        max_diff_lines: Maximum number of diff lines per file.
        max_notebook_cells: Maximum number of notebook cells per file.

    Returns:
        Formatted commit string.
    """
    lines = []

    # Commit header
    lines.append(f"[{index}/{total}] {commit.full_repo_name}")
    lines.append("-" * 40)

    # Metadata
    lines.append(f"Date:    {format_datetime(commit.author_date)}")
    lines.append(f"SHA:     {commit.sha}")
    lines.append(f"Author:  {commit.author_name} <{commit.author_email}>")
    lines.append(f"URL:     {commit.html_url}")

    # Message
    lines.append("")
    lines.append("Message:")
    lines.append(commit.message)

    # Statistics
    lines.append("")
    stats_parts = [
        f"{commit.files_changed} file{'s' if commit.files_changed != 1 else ''} changed",
        f"+{commit.total_additions} insertion{'s' if commit.total_additions != 1 else ''}",
        f"-{commit.total_deletions} deletion{'s' if commit.total_deletions != 1 else ''}",
    ]
    lines.append(f"Stats: {', '.join(stats_parts)}")

    # Changed files
    if commit.files:
        lines.append("")
        lines.append("Changed Files:")

        for file in commit.files:
            lines.append(format_file_change(file, max_diff_lines, max_notebook_cells))

    return "\n".join(lines)


def format_report(
    commits: List[CommitData],
    max_diff_lines: Optional[int] = None,
    max_notebook_cells: Optional[int] = None,
) -> str:
    """
    Format a complete report for multiple commits.

    Args:
        commits: List of commit data.
        max_diff_lines: Maximum number of diff lines per file.
        max_notebook_cells: Maximum number of notebook cells per file.

    Returns:
        Formatted report string.
    """
    lines = []
    separator = "=" * 40

    # Report header
    lines.append(separator)
    commit_count = len(commits)
    lines.append(f"Commit Report ({commit_count} commit{'s' if commit_count != 1 else ''})")
    lines.append(f"Generated: {format_datetime(datetime.now(timezone.utc))}")
    lines.append(separator)

    # Format each commit
    for i, commit in enumerate(commits, 1):
        lines.append("")
        lines.append(format_commit(commit, i, len(commits), max_diff_lines, max_notebook_cells))
        lines.append("")
        lines.append(separator)

    return "\n".join(lines)
