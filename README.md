# commit2report

A CLI tool that generates text reports from GitHub commit URLs. Outputs in a format optimized for copy-paste into OneNote and similar applications.

## Features

- Batch processing of multiple commit URLs
- Supports both private and public repositories
- Detailed reports including changed file lists and diff contents
- Jupyter Notebook changes displayed as summary (additions/deletions count)
- Option to limit diff line count
- Plain text output for easy copy-paste

## Installation

```bash
# Clone the repository
git clone https://github.com/NaotoKubota/commit2report.git
cd commit2report

# Install
pip install -e .
```

## Setup

1. Create a GitHub Personal Access Token (PAT)
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Scopes: `repo` (for private repositories) or `public_repo` (for public only)

2. Set the environment variable
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env file to set your token
   GITHUB_TOKEN=ghp_your_token_here
   ```

   Or set the environment variable directly:
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

## Usage

### Basic Usage

```bash
# Single commit
commit2report https://github.com/owner/repo/commit/abc1234

# Multiple commits (can be from different repositories)
commit2report \
  https://github.com/owner/repo1/commit/abc1234 \
  https://github.com/owner/repo2/commit/def5678
```

### Load URLs from File

```bash
# List URLs in commits.txt, one per line
commit2report --file commits.txt
```

Example commits.txt:
```
https://github.com/owner/repo1/commit/abc1234
https://github.com/owner/repo2/commit/def5678
https://github.com/owner/repo3/commit/ghi9012
```

### Limit Diff Lines

```bash
# Limit diff to maximum 50 lines per file
commit2report --max-diff-lines 50 https://github.com/owner/repo/commit/abc1234
```

### Verbose Mode

```bash
# Enable verbose (debug) output
commit2report --verbose https://github.com/owner/repo/commit/abc1234
```

### Combining Options

```bash
# Load URLs from file + diff limit + extra URL
commit2report --file commits.txt --max-diff-lines 100 https://github.com/extra/repo/commit/xyz
```

## Output Example

```
========================================
Commit Report (2 commits)
Generated: 2026-02-02 10:30:00
========================================

[1/2] owner/repo1
----------------------------------------
Date:    2026-01-15 14:30:25
SHA:     abc1234567890abcdef1234567890abcdef123456
Author:  John Doe <john@example.com>
URL:     https://github.com/owner/repo1/commit/abc1234

Message:
feat: Add login feature

- Support OAuth2 authentication
- Implement session management

Stats: 2 files changed, +80 insertions, -5 deletions

Changed Files:
────────────────────────────────────────
[M] src/auth/login.py (+70, -5)
────────────────────────────────────────
@@ -10,5 +10,15 @@
 def authenticate():
-    pass
+    """Authentication process"""
+    token = get_token()
+    return validate(token)

────────────────────────────────────────
[A] src/auth/session.py (+10, -0)
────────────────────────────────────────
+"""Session management module"""
+class Session:
+    pass

========================================

[2/2] owner/repo2
...
```

## File Status Legend

- `[A]` - Added
- `[M]` - Modified
- `[D]` - Deleted
- `[R]` - Renamed

## Troubleshooting

### "GITHUB_TOKEN is not set" Error

The `GITHUB_TOKEN` environment variable is not set. Refer to the Setup section.

### "401 Unauthorized" Error

The token is invalid or expired. Generate a new token.

### "404 Not Found" Error

- The repository does not exist or you do not have access permissions
- For private repositories, the token requires the `repo` scope

### Rate Limit Error

You have reached the GitHub API rate limit. Please wait a while and try again.

## License

MIT License
