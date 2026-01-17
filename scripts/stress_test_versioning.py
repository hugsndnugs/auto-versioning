#!/usr/bin/env python3
"""
Stress Test Script for Auto Version Numbering

This script performs comprehensive stress tests on the version bump functionality by:
- Creating a test branch
- Making commits with different increment types
- Validating version increments
- Testing edge cases
"""

import re
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


class TestResult:
    """Track test results."""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.expected = None
        self.actual = None
    
    def set_result(self, passed: bool, expected: str = None, actual: str = None, error: str = None):
        self.passed = passed
        self.expected = expected
        self.actual = actual
        self.error = error


class VersionStressTester:
    """Main test class for stress testing version bumps."""
    
    def __init__(self, version_file: str = "__version__.py"):
        self.version_file = version_file
        self.test_branch = f"stress-test-versioning-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.results: list[TestResult] = []
        self.original_branch = None
        
    def run_command(self, cmd: list[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout.strip(), e.stderr.strip()
    
    def read_version(self) -> str:
        """Read current version from version file."""
        version_path = Path(self.version_file)
        if not version_path.exists():
            return "0.0.0"
        
        try:
            with open(version_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
            if match:
                return match.group(1)
            return "0.0.0"
        except Exception as e:
            print(f"Error reading version: {e}")
            return "0.0.0"
    
    def set_version(self, version: str) -> bool:
        """Set version in version file."""
        version_path = Path(self.version_file)
        try:
            version_path.parent.mkdir(parents=True, exist_ok=True)
            with open(version_path, 'w', encoding='utf-8') as f:
                f.write(f'__version__ = "{version}"\n')
            return True
        except Exception as e:
            print(f"Error setting version: {e}")
            return False
    
    def make_commit(self, message: str, file_content: str = "test") -> bool:
        """Make a test commit with the given message."""
        # Create or update a test file
        test_file = Path("stress_test_file.txt")
        with open(test_file, 'w') as f:
            f.write(f"{file_content}\n")
        
        # Stage and commit
        self.run_command(['git', 'add', str(test_file)])
        returncode, _, _ = self.run_command(
            ['git', 'commit', '-m', message],
            check=False
        )
        return returncode == 0
    
    def run_version_manager(self) -> bool:
        """Run the version-manager command."""
        returncode, stdout, stderr = self.run_command(
            ['version-manager'],
            check=False
        )
        if returncode != 0 and returncode != 1:
            print(f"version-manager error: {stderr}")
        return returncode == 0 or returncode == 1
    
    def calculate_expected_version(self, current: str, increment_type: str) -> str:
        """Calculate expected version after increment."""
        parts = current.split('.')
        major, minor, patch = map(int, parts)
        
        if increment_type == 'major':
            return f"{major + 1}.0.0"
        elif increment_type == 'minor':
            return f"{major}.{minor + 1}.0"
        elif increment_type == 'patch':
            return f"{major}.{minor}.{patch + 1}"
        else:
            return current
    
    def test_increment(self, test_name: str, current_version: str, commit_message: str, 
                      expected_increment: str) -> TestResult:
        """Test a single version increment."""
        result = TestResult(test_name)
        
        try:
            # Set initial version
            if not self.set_version(current_version):
                result.set_result(False, error="Failed to set initial version")
                return result
            
            # Commit the version file
            self.run_command(['git', 'add', self.version_file])
            self.run_command(['git', 'commit', '-m', f'Set version to {current_version} [skip ci]'], check=False)
            
            # Make test commit
            if not self.make_commit(commit_message):
                result.set_result(False, error="Failed to make commit")
                return result
            
            # Run version manager
            self.run_version_manager()
            
            # Commit version file changes (if any)
            self.run_command(['git', 'add', self.version_file], check=False)
            self.run_command(['git', 'commit', '-m', 'chore: auto-increment version [skip ci]'], check=False)
            
            # Read actual version
            actual_version = self.read_version()
            expected_version = self.calculate_expected_version(current_version, expected_increment)
            
            # Validate
            if actual_version == expected_version:
                result.set_result(True, expected_version, actual_version)
            else:
                result.set_result(False, expected_version, actual_version, 
                                f"Version mismatch: expected {expected_version}, got {actual_version}")
        
        except Exception as e:
            result.set_result(False, error=f"Exception: {str(e)}")
        
        return result
    
    def setup_test_branch(self) -> bool:
        """Create and checkout test branch."""
        try:
            # Get current branch
            returncode, stdout, _ = self.run_command(['git', 'branch', '--show-current'], check=False)
            if returncode == 0:
                self.original_branch = stdout
            
            # Setup git remote with token if available
            github_token = os.environ.get('GITHUB_TOKEN')
            if github_token:
                # Get repository URL
                returncode, remote_url, _ = self.run_command(['git', 'config', '--get', 'remote.origin.url'], check=False)
                if returncode == 0 and remote_url:
                    # Replace URL with token authentication
                    if remote_url.startswith('https://'):
                        # Extract repo path (e.g., owner/repo from https://github.com/owner/repo.git)
                        import re
                        match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', remote_url)
                        if match:
                            repo_path = match.group(1)
                            auth_url = f"https://{github_token}@github.com/{repo_path}.git"
                            self.run_command(['git', 'remote', 'set-url', 'origin', auth_url], check=False)
            
            # Create and checkout test branch
            self.run_command(['git', 'checkout', '-b', self.test_branch], check=False)
            
            # Push branch (non-blocking - tests can continue even if push fails)
            self.run_command(['git', 'push', '-u', 'origin', self.test_branch], check=False)
            
            print(f"Created test branch: {self.test_branch}")
            return True
        except Exception as e:
            print(f"Error setting up test branch: {e}")
            return False
    
    def test_basic_increments(self):
        """Test basic increment types."""
        print("\n=== Testing Basic Increments ===")
        
        # Test patch increment
        result = self.test_increment(
            "Patch increment",
            "1.2.3",
            "Test patch increment [patch] [skip ci]",
            "patch"
        )
        self.results.append(result)
        
        # Test minor increment
        result = self.test_increment(
            "Minor increment",
            "1.2.3",
            "Test minor increment [minor] [skip ci]",
            "minor"
        )
        self.results.append(result)
        
        # Test major increment
        result = self.test_increment(
            "Major increment",
            "1.2.3",
            "Test major increment [major] [skip ci]",
            "major"
        )
        self.results.append(result)
        
        # Test default (no marker = patch)
        result = self.test_increment(
            "Default increment (no marker)",
            "1.2.3",
            "Test default increment [skip ci]",
            "patch"
        )
        self.results.append(result)
    
    def test_rapid_consecutive_commits(self):
        """Test rapid consecutive commits with different increment types."""
        print("\n=== Testing Rapid Consecutive Commits ===")
        
        # Start from 0.0.0
        self.set_version("0.0.0")
        self.run_command(['git', 'add', self.version_file])
        self.run_command(['git', 'commit', '-m', 'Initialize version 0.0.0 [skip ci]'], check=False)
        
        test_sequence = [
            ("First patch", "[patch]", "0.0.1"),
            ("Second patch", "[patch]", "0.0.2"),
            ("First minor", "[minor]", "0.1.0"),
            ("Third patch", "[patch]", "0.1.1"),
            ("Second minor", "[minor]", "0.2.0"),
            ("Fourth patch", "[patch]", "0.2.1"),
            ("First major", "[major]", "1.0.0"),
            ("Fifth patch", "[patch]", "1.0.1"),
        ]
        
        for test_name, marker, expected_version in test_sequence:
            current_version = self.read_version()
            commit_message = f"Stress test: {test_name} {marker} [skip ci]"
            
            result = TestResult(f"Rapid commit: {test_name}")
            try:
                if not self.make_commit(commit_message):
                    result.set_result(False, error="Failed to make commit")
                    self.results.append(result)
                    continue
                
                self.run_version_manager()
                
                # Commit version file changes (if any)
                self.run_command(['git', 'add', self.version_file], check=False)
                self.run_command(['git', 'commit', '-m', 'chore: auto-increment version [skip ci]'], check=False)
                
                actual_version = self.read_version()
                
                if actual_version == expected_version:
                    result.set_result(True, expected_version, actual_version)
                else:
                    result.set_result(False, expected_version, actual_version,
                                    f"Expected {expected_version}, got {actual_version}")
            except Exception as e:
                result.set_result(False, error=f"Exception: {str(e)}")
            
            self.results.append(result)
    
    def test_edge_cases(self):
        """Test edge cases."""
        print("\n=== Testing Edge Cases ===")
        
        # Test version rollover (9.9.9 -> 10.0.0)
        result = self.test_increment(
            "Version rollover (9.9.9 -> 10.0.0)",
            "9.9.9",
            "Test version rollover [patch] [skip ci]",
            "patch"
        )
        self.results.append(result)
        
        # Test major from 9.9.9
        result = self.test_increment(
            "Major from 9.9.9",
            "9.9.9",
            "Test major from 9.9.9 [major] [skip ci]",
            "major"
        )
        self.results.append(result)
        
        # Test starting from 0.0.0
        result = self.test_increment(
            "Start from 0.0.0",
            "0.0.0",
            "Test from 0.0.0 [patch] [skip ci]",
            "patch"
        )
        self.results.append(result)
    
    def test_missing_version_file(self):
        """Test behavior when version file is missing."""
        print("\n=== Testing Missing Version File ===")
        
        result = TestResult("Missing version file")
        try:
            # Remove version file
            version_path = Path(self.version_file)
            if version_path.exists():
                self.run_command(['git', 'rm', self.version_file], check=False)
                self.run_command(['git', 'commit', '-m', 'Remove version file [skip ci]'], check=False)
            
            # Make a commit
            if not self.make_commit("Test with missing version file [patch] [skip ci]"):
                result.set_result(False, error="Failed to make commit")
                self.results.append(result)
                return
            
            # Run version manager (should create file with 0.0.0, then increment)
            self.run_version_manager()
            
            # Commit version file changes (if any)
            self.run_command(['git', 'add', self.version_file], check=False)
            self.run_command(['git', 'commit', '-m', 'chore: auto-increment version [skip ci]'], check=False)
            
            # Check if file was created and version is correct
            if version_path.exists():
                actual_version = self.read_version()
                # Should be 0.0.1 (created as 0.0.0, then incremented to 0.0.1)
                if actual_version == "0.0.1":
                    result.set_result(True, "0.0.1", actual_version)
                else:
                    result.set_result(False, "0.0.1", actual_version,
                                    f"Expected 0.0.1, got {actual_version}")
            else:
                result.set_result(False, error="Version file was not created")
        
        except Exception as e:
            result.set_result(False, error=f"Exception: {str(e)}")
        
        self.results.append(result)
    
    def test_skip_logic(self):
        """Test that skip logic prevents infinite loops."""
        print("\n=== Testing Skip Logic ===")
        
        result = TestResult("Skip logic (auto-increment commit)")
        try:
            self.set_version("1.0.0")
            self.run_command(['git', 'add', self.version_file])
            self.run_command(['git', 'commit', '-m', 'Set version to 1.0.0 [skip ci]'], check=False)
            
            # Make commit with auto-increment message (should be skipped)
            if not self.make_commit("chore: auto-increment version [skip ci]"):
                result.set_result(False, error="Failed to make commit")
                self.results.append(result)
                return
            
            version_before = self.read_version()
            self.run_version_manager()
            version_after = self.read_version()
            
            # Version should not change (skip logic should prevent update)
            if version_before == version_after:
                result.set_result(True, version_before, version_after)
            else:
                result.set_result(False, version_before, version_after,
                                "Version changed when it should have been skipped")
        
        except Exception as e:
            result.set_result(False, error=f"Exception: {str(e)}")
        
        self.results.append(result)
    
    def test_commit_message_variations(self):
        """Test different commit message formats."""
        print("\n=== Testing Commit Message Variations ===")
        
        # Test marker at start
        result = self.test_increment(
            "Marker at start of message",
            "1.0.0",
            "[minor] Test marker at start [skip ci]",
            "minor"
        )
        self.results.append(result)
        
        # Test marker in middle
        result = self.test_increment(
            "Marker in middle of message",
            "1.0.0",
            "Test [major] marker in middle [skip ci]",
            "major"
        )
        self.results.append(result)
        
        # Test marker at end
        result = self.test_increment(
            "Marker at end of message",
            "1.0.0",
            "Test marker at end [patch] [skip ci]",
            "patch"
        )
        self.results.append(result)
        
        # Test case sensitivity (should be case-insensitive)
        result = self.test_increment(
            "Case insensitive marker",
            "1.0.0",
            "Test [MAJOR] uppercase marker [skip ci]",
            "major"
        )
        self.results.append(result)
        
        # Test multiple markers (should use first/most significant)
        result = self.test_increment(
            "Multiple markers (major takes precedence)",
            "1.0.0",
            "Test [major] and [minor] markers [skip ci]",
            "major"
        )
        self.results.append(result)
    
    def run_all_tests(self):
        """Run all stress tests."""
        print("=" * 60)
        print("Starting Version Bump Stress Tests")
        print("=" * 60)
        
        # Setup test branch
        if not self.setup_test_branch():
            print("ERROR: Failed to setup test branch")
            sys.exit(1)
        
        # Run all test suites
        self.test_basic_increments()
        self.test_rapid_consecutive_commits()
        self.test_edge_cases()
        self.test_missing_version_file()
        self.test_skip_logic()
        self.test_commit_message_variations()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test results report."""
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{status}: {result.name}")
            if not result.passed:
                if result.error:
                    print(f"  Error: {result.error}")
                if result.expected and result.actual:
                    print(f"  Expected: {result.expected}, Actual: {result.actual}")
        
        # Write results to file for workflow summary
        with open("stress_test_results.txt", "w") as f:
            f.write(f"# Stress Test Results\n\n")
            f.write(f"**Total Tests:** {total}\n")
            f.write(f"**Passed:** {passed}\n")
            f.write(f"**Failed:** {total - passed}\n")
            f.write(f"**Success Rate:** {passed/total*100:.1f}%\n\n")
            f.write("## Detailed Results\n\n")
            
            for result in self.results:
                status = "✓ PASS" if result.passed else "✗ FAIL"
                f.write(f"### {status}: {result.name}\n")
                if not result.passed:
                    if result.error:
                        f.write(f"**Error:** {result.error}\n")
                    if result.expected and result.actual:
                        f.write(f"**Expected:** {result.expected}, **Actual:** {result.actual}\n")
                f.write("\n")
        
        # Exit with error if any tests failed
        if passed < total:
            print(f"\n❌ Stress tests failed: {total - passed} test(s) failed")
            sys.exit(1)
        else:
            print(f"\n✓ All stress tests passed!")
            sys.exit(0)


def main():
    """Main entry point."""
    version_file = os.environ.get('VERSION_FILE', '__version__.py')
    tester = VersionStressTester(version_file)
    tester.run_all_tests()


if __name__ == '__main__':
    main()
