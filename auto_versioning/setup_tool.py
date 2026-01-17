#!/usr/bin/env python3
"""
Setup tool for auto-versioning.

This script sets up the auto-versioning tool in a repository by:
1. Installing the GitHub Actions workflow
2. Creating the initial __version__.py file if it doesn't exist
"""

import os
import shutil
import sys
from pathlib import Path


def get_package_dir():
    """Get the directory where the package is installed."""
    return Path(__file__).parent


def get_template_path():
    """Get the path to the workflow template."""
    package_dir = get_package_dir()
    return package_dir / 'templates' / 'auto-version.yml'


def install_workflow(workflow_dir: Path, template_path: Path) -> bool:
    """
    Install the GitHub Actions workflow file.
    
    Args:
        workflow_dir: Directory where .github/workflows should be created
        template_path: Path to the workflow template
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create .github/workflows directory if it doesn't exist
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflow_dir / 'auto-version.yml'
        
        # Read template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Check if workflow already exists
        if workflow_file.exists():
            response = input(f"Workflow file {workflow_file} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Skipping workflow installation.")
                return False
        
        # Write workflow file
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✓ Installed GitHub Actions workflow to {workflow_file}")
        return True
    except Exception as e:
        print(f"Error installing workflow: {e}")
        return False


def create_version_file(version_file_path: Path, initial_version: str = "0.0.0") -> bool:
    """
    Create the initial __version__.py file if it doesn't exist.
    
    Args:
        version_file_path: Path where __version__.py should be created
        initial_version: Initial version string (default: "0.0.0")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if version_file_path.exists():
            print(f"✓ Version file already exists at {version_file_path}")
            return True
        
        # Create directory if needed
        version_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create version file
        with open(version_file_path, 'w', encoding='utf-8') as f:
            f.write(f'__version__ = "{initial_version}"\n')
        
        print(f"✓ Created version file at {version_file_path} with version {initial_version}")
        return True
    except Exception as e:
        print(f"Error creating version file: {e}")
        return False


def main():
    """Main setup function."""
    # Get current working directory (should be repository root)
    repo_root = Path.cwd()
    
    # Get template path
    template_path = get_template_path()
    
    if not template_path.exists():
        print(f"Error: Template file not found at {template_path}")
        print("This may indicate the package was not installed correctly.")
        sys.exit(1)
    
    # Determine paths
    workflow_dir = repo_root / '.github' / 'workflows'
    version_file_path = repo_root / '__version__.py'
    
    # Allow custom version file location via environment variable
    custom_version_file = os.environ.get('VERSION_FILE')
    if custom_version_file:
        version_file_path = repo_root / custom_version_file
    
    print("Setting up auto-versioning in this repository...")
    print(f"Repository root: {repo_root}")
    print()
    
    # Install workflow
    workflow_installed = install_workflow(workflow_dir, template_path)
    
    # Create version file
    version_created = create_version_file(version_file_path)
    
    print()
    if workflow_installed and version_created:
        print("✓ Setup complete!")
        print()
        print("Next steps:")
        print("1. Commit the changes:")
        print(f"   git add .github/workflows/auto-version.yml {'__version__.py' if version_created else ''}")
        print("   git commit -m 'Add auto-versioning setup [patch]'")
        print("2. Push to GitHub to trigger the workflow")
        sys.exit(0)
    else:
        print("Setup completed with some issues. Please review the messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
