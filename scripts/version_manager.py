#!/usr/bin/env python3
"""
Version Manager Script for Auto Version Numbering

This script reads the current version from __version__.py, parses commit messages
for version increment markers ([major], [minor], [patch]), and updates the version file.
"""

import re
import sys
import os
from pathlib import Path


def read_current_version(version_file_path: str) -> str:
    """Read the current version from __version__.py file."""
    version_file = Path(version_file_path)
    
    if not version_file.exists():
        return "0.0.0"
    
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Match __version__ = "x.y.z" or __version__ = 'x.y.z'
            match = re.search(r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
            if match:
                return match.group(1)
            else:
                print(f"Warning: Could not parse version from {version_file_path}, defaulting to 0.0.0")
                return "0.0.0"
    except Exception as e:
        print(f"Error reading version file: {e}, defaulting to 0.0.0")
        return "0.0.0"


def increment_version(current_version: str, increment_type: str) -> str:
    """
    Increment version based on type.
    
    Args:
        current_version: Current version string (e.g., "1.2.3")
        increment_type: Type of increment - 'major', 'minor', or 'patch'
    
    Returns:
        New version string
    """
    parts = current_version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current_version}. Expected MAJOR.MINOR.PATCH")
    
    major, minor, patch = map(int, parts)
    
    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")
    
    return f"{major}.{minor}.{patch}"


def get_latest_commit_message() -> str:
    """Get the latest commit message from git."""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit message: {e}")
        return ""
    except FileNotFoundError:
        print("Warning: git not found, cannot read commit message")
        return ""


def parse_commit_message_for_increment(commit_message: str) -> str:
    """
    Parse commit message for version increment markers.
    
    Looks for [major], [minor], or [patch] in the commit message.
    Returns the increment type, defaulting to 'patch' if no marker found.
    
    Returns None if the commit message indicates this is already a version update commit
    (to prevent infinite loops).
    """
    commit_message_lower = commit_message.lower()
    
    # Skip if this is already a version update commit
    if 'auto-increment version' in commit_message_lower or '[skip ci]' in commit_message_lower:
        # If it's a version commit but also has an increment marker, still process it
        pass
    
    if '[major]' in commit_message_lower:
        return 'major'
    elif '[minor]' in commit_message_lower:
        return 'minor'
    elif '[patch]' in commit_message_lower:
        return 'patch'
    else:
        return 'patch'  # Default to patch increment


def should_skip_version_update(commit_message: str) -> bool:
    """
    Check if we should skip version update to prevent infinite loops.
    
    Returns True if the commit message indicates this is already a version update commit.
    """
    commit_message_lower = commit_message.lower()
    # Skip if this commit is specifically a version update and has no increment markers
    if ('auto-increment version' in commit_message_lower or 
        'chore: auto-increment' in commit_message_lower) and \
        not any(marker in commit_message_lower for marker in ['[major]', '[minor]', '[patch]']):
        return True
    return False


def update_version_file(version_file_path: str, new_version: str) -> bool:
    """
    Update the version file with the new version.
    
    Returns True if the file was updated, False otherwise.
    """
    version_file = Path(version_file_path)
    
    # Create directory if it doesn't exist
    version_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the version line
            new_content = re.sub(
                r'__version__\s*=\s*["\'][^"\']+["\']',
                f'__version__ = "{new_version}"',
                content
            )
            
            # If no version line found, add it at the end or create new file
            if new_content == content:
                new_content = f'__version__ = "{new_version}"\n'
        else:
            new_content = f'__version__ = "{new_version}"\n'
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        print(f"Error updating version file: {e}")
        return False


def main():
    """Main function to handle version incrementing."""
    # Default version file path
    version_file_path = os.environ.get('VERSION_FILE', '__version__.py')
    
    # Read current version
    current_version = read_current_version(version_file_path)
    print(f"Current version: {current_version}")
    
    # Get commit message and determine increment type
    commit_message = get_latest_commit_message()
    
    # Skip if this is already a version update commit (prevent infinite loops)
    if should_skip_version_update(commit_message):
        print("Skipping version update - commit appears to be an auto-version update")
        sys.exit(0)
    
    increment_type = parse_commit_message_for_increment(commit_message)
    
    print(f"Commit message: {commit_message[:50]}...")
    print(f"Increment type: {increment_type}")
    
    # Increment version
    new_version = increment_version(current_version, increment_type)
    print(f"New version: {new_version}")
    
    # Update version file
    if update_version_file(version_file_path, new_version):
        print(f"Successfully updated {version_file_path} to version {new_version}")
        # Exit with 0 if version changed, 1 if unchanged
        if current_version != new_version:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"Failed to update version file")
        sys.exit(1)


if __name__ == '__main__':
    main()
