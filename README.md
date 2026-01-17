# Auto Version Numbering via GitHub Actions

Automatically increment semantic version numbers (MAJOR.MINOR.PATCH) on every commit using GitHub Actions. This workflow detects version increment markers in commit messages and updates a Python version file accordingly.

## Features

- ✅ **Automatic versioning** - No manual version updates required
- ✅ **Semantic versioning** - Follows MAJOR.MINOR.PATCH format
- ✅ **Commit message based** - Control version increments via commit messages
- ✅ **All branches** - Works on every branch automatically
- ✅ **Python integration** - Updates `__version__.py` file for easy import

## How It Works

The workflow runs automatically on every push to any branch:

1. Detects version increment markers in commit messages (`[major]`, `[minor]`, `[patch]`)
2. Reads the current version from `__version__.py`
3. Increments the appropriate version component
4. Updates `__version__.py` with the new version
5. Commits and pushes the version update back to the repository

## Setup

### Prerequisites

- A GitHub repository
- Python 3.x (used by the workflow)

### Installation

1. **Clone or initialize your repository**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Ensure the required files exist**
   - `__version__.py` - Version file (created automatically if missing, starts at `0.0.0`)
   - `scripts/version_manager.py` - Version management script
   - `.github/workflows/auto-version.yml` - GitHub Actions workflow

3. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add auto-versioning workflow [patch]"
   git push
   ```

4. **Verify workflow runs**
   - Go to your repository on GitHub
   - Navigate to the "Actions" tab
   - You should see the "Auto Version Numbering" workflow running

## Usage

### Version Increment Markers

Control version increments by including markers in your commit messages:

#### Major Version (Breaking Changes)
```bash
git commit -m "Refactor API interface [major]"
```
Increments: `1.2.3` → `2.0.0`

#### Minor Version (New Features)
```bash
git commit -m "Add user authentication feature [minor]"
```
Increments: `1.2.3` → `1.3.0`

#### Patch Version (Bug Fixes)
```bash
git commit -m "Fix login bug [patch]"
```
Increments: `1.2.3` → `1.2.4`

#### Default (Patch)
If no marker is specified, the patch version is incremented:
```bash
git commit -m "Update documentation"
```
Increments: `1.2.3` → `1.2.4`

### Accessing the Version

The version is stored in `__version__.py` and can be imported in your Python code:

```python
from __version__ import __version__

print(f"Current version: {__version__}")
# Output: Current version: 1.2.3
```

Or if the file is in a subdirectory:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from __version__ import __version__
```

### Version File Format

The `__version__.py` file follows a standard Python format:

```python
__version__ = "1.2.3"
```

## Examples

### Example Workflow

```bash
# Start with version 0.0.0
git commit -m "Initial commit"
# Version becomes: 0.0.1 (default patch increment)

git commit -m "Add user model [minor]"
# Version becomes: 0.1.0

git commit -m "Fix typo in README [patch]"
# Version becomes: 0.1.1

git commit -m "Add authentication endpoints [minor]"
# Version becomes: 0.2.0

git commit -m "Change API response format [major]"
# Version becomes: 1.0.0

git commit -m "Update dependencies"
# Version becomes: 1.0.1 (default patch increment)
```

### Commit Message Best Practices

Good commit messages with version markers:

```bash
git commit -m "feat: Add email verification [minor]"
git commit -m "fix: Resolve memory leak in image processing [patch]"
git commit -m "BREAKING: Remove deprecated endpoints [major]"
git commit -m "docs: Update API documentation"
```

## Configuration

### Custom Version File Location

By default, the workflow looks for `__version__.py` in the repository root. To use a different location, set the `VERSION_FILE` environment variable in the workflow:

```yaml
- name: Run version manager
  env:
    VERSION_FILE: 'src/__version__.py'
  run: |
    python scripts/version_manager.py
```

### Workflow Permissions

The workflow requires `contents: write` permission to commit version updates back to the repository. This is already configured in `.github/workflows/auto-version.yml`:

```yaml
permissions:
  contents: write
```

### Preventing Re-triggers

The workflow includes logic to prevent infinite loops:

- Version update commits include `[skip ci]` in the commit message
- The version manager script skips processing if the commit is already a version update

## Workflow Details

### When It Runs

The workflow triggers on every push to any branch:

```yaml
on:
  push:
    branches:
      - '**'  # All branches
```

### Workflow Steps

1. **Checkout** - Full repository checkout with complete history
2. **Set up Python** - Configures Python environment
3. **Run Version Manager** - Executes the version increment script
4. **Check Changes** - Detects if version file was modified
5. **Commit & Push** - Commits and pushes version update if changed

### Manual Execution

You can also run the version manager script locally:

```bash
python scripts/version_manager.py
```

The script will:
- Read the current version from `__version__.py`
- Get the latest commit message
- Determine the increment type
- Update the version file
- Exit with code 0 if version changed, 1 if unchanged

## Troubleshooting

### Version Not Updating

**Issue**: Version file isn't being updated after commits.

**Solutions**:
- Check that the workflow file exists at `.github/workflows/auto-version.yml`
- Verify the workflow ran in the GitHub Actions tab
- Ensure commit messages include version markers (or use default patch behavior)
- Check workflow logs for errors

### Infinite Loop Warning

**Issue**: Workflow keeps triggering version updates.

**Solutions**:
- The workflow should automatically skip version update commits
- Check that version update commits include `[skip ci]`
- Verify the `should_skip_version_update()` function in the script

### Version File Not Found

**Issue**: Error about missing `__version__.py`.

**Solutions**:
- The script will create the file automatically if missing (starts at `0.0.0`)
- Ensure you have write permissions in the repository
- Check the file path is correct (default is repository root)

### Permission Errors

**Issue**: Workflow fails with permission errors when pushing.

**Solutions**:
- Verify `permissions: contents: write` is set in the workflow
- Check that `GITHUB_TOKEN` is available (automatically provided by GitHub Actions)
- Ensure the workflow isn't restricted by branch protection rules

### Multiple Commits in One Push

**Issue**: How does versioning work with multiple commits?

**Solution**: The workflow checks the most recent commit message only. If you push multiple commits, only the latest commit's message is used for version increment determination.

## File Structure

```
.
├── __version__.py                 # Version file (created/updated automatically)
├── scripts/
│   └── version_manager.py        # Version management script
├── .github/
│   └── workflows/
│       └── auto-version.yml      # GitHub Actions workflow
└── README.md                      # This file
```

## Version Increment Rules

| Commit Message Contains | Current Version | New Version |
|------------------------|-----------------|-------------|
| `[major]` | `1.2.3` | `2.0.0` |
| `[minor]` | `1.2.3` | `1.3.0` |
| `[patch]` | `1.2.3` | `1.2.4` |
| No marker | `1.2.3` | `1.2.4` (defaults to patch) |

## Contributing

To contribute improvements to this workflow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Commit with appropriate version markers
5. Submit a pull request

## License

This project is open source and available under the MIT License (or your preferred license).

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the workflow logs in the Actions tab
- Review the troubleshooting section above

---

**Note**: This workflow automatically handles version updates on every commit. Make sure to include version increment markers (`[major]`, `[minor]`, `[patch]`) in your commit messages when you want to control version increments beyond the default patch behavior.
