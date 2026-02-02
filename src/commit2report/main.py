"""CLI entry point for commit2report."""

import logging
import sys
from typing import List, Optional

import click

from . import __version__
from .auth import AuthenticationError, get_github_client
from .fetcher import FetchError, fetch_commits
from .formatter import format_report
from .parser import ParseError, load_urls_from_file, parse_commit_urls

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging format and level."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(format_str, datefmt=date_format))
    
    # Configure root logger
    root_logger = logging.getLogger("commit2report")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def collect_urls(urls: tuple, file: Optional[str]) -> List[str]:
    """
    Collect URLs from command line arguments and file.

    Args:
        urls: URLs provided as command line arguments.
        file: Path to file containing URLs.

    Returns:
        Combined list of URLs.

    Raises:
        ParseError: If no URLs are provided.
    """
    all_urls = list(urls)

    if file:
        file_urls = load_urls_from_file(file)
        all_urls.extend(file_urls)

    if not all_urls:
        raise ParseError(
            "No commit URLs provided.\n"
            "Please provide URLs as arguments or use --file option."
        )

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


@click.command()
@click.argument("urls", nargs=-1)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True),
    help="File containing commit URLs (one per line).",
)
@click.option(
    "--max-diff-lines",
    "-m",
    type=int,
    default=None,
    help="Maximum number of diff lines to show per file (default: unlimited).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output (debug logging).",
)
@click.version_option(version=__version__, prog_name="commit2report")
def cli(urls: tuple, file: Optional[str], max_diff_lines: Optional[int], verbose: bool):
    """
    Generate text reports from GitHub commit URLs.

    Provide one or more GitHub commit URLs as arguments, or use --file to
    read URLs from a file. The report is printed to stdout in a format
    suitable for copy-paste into OneNote or other text editors.

    Example:

        commit2report https://github.com/owner/repo/commit/abc123

        commit2report --file commits.txt --max-diff-lines 50
    """
    # Setup logging
    setup_logging(verbose)

    try:
        # Collect all URLs
        all_urls = collect_urls(urls, file)

        # Parse URLs
        logger.info(f"Parsing {len(all_urls)} commit URL(s)...")
        commit_infos = parse_commit_urls(all_urls)
        logger.debug(f"Parsed URLs: {[c.full_repo_name for c in commit_infos]}")

        # Authenticate
        logger.info("Authenticating with GitHub...")
        client = get_github_client()

        # Fetch commit data
        logger.info("Fetching commit data...")
        commits = fetch_commits(client, commit_infos)
        logger.debug(f"Fetched {len(commits)} commit(s)")

        # Generate report
        logger.info("Generating report...")
        report = format_report(commits, max_diff_lines)

        # Output report to stdout
        logger.info("Done!")
        click.echo("")  # Empty line before report
        click.echo(report)

    except ParseError as e:
        logger.error(f"Parse Error: {e}")
        sys.exit(1)
    except AuthenticationError as e:
        logger.error(f"Authentication Error: {e}")
        sys.exit(1)
    except FetchError as e:
        logger.error(f"Fetch Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Aborted by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
