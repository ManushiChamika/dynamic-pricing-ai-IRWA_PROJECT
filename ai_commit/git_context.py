"""Git repository context and operations."""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


class GitError(Exception):
    """Raised when Git operations fail."""
    pass


@dataclass
class GitContext:
    """Git repository context information."""
    
    def __init__(self):
        """Initialize Git context and validate repository."""
        self._validate_git_repo()
        
    def _validate_git_repo(self) -> None:
        """Ensure we're in a valid Git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise GitError("Not inside a Git repository")
            
    def _run_git_command(self, args: List[str], timeout: int = 30) -> str:
        """Run a git command and return stdout."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: {' '.join(args)}\n{e.stderr}")
        except subprocess.TimeoutExpired:
            raise GitError(f"Git command timed out: {' '.join(args)}")
        except FileNotFoundError:
            raise GitError("Git command not found")
            
    def has_staged_changes(self) -> bool:
        """Check if there are staged changes."""
        try:
            self._run_git_command(["diff", "--cached", "--quiet"])
            return False  # No staged changes
        except GitError:
            return True  # Has staged changes
            
    def stage_all(self) -> None:
        """Stage all changes."""
        self._run_git_command(["add", "."])
        
    def has_conflicts(self) -> bool:
        """Check if there are merge conflicts."""
        try:
            conflicts = self._run_git_command(["ls-files", "-u"])
            return bool(conflicts.strip())
        except GitError:
            return False
            
    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        except GitError:
            return "unknown"
            
    def get_staged_files(self) -> List[tuple[str, str]]:
        """Get list of staged files with their status."""
        try:
            output = self._run_git_command(["diff", "--cached", "--name-status"])
            files = []
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        status, filename = parts
                        files.append((status, filename))
            return files
        except GitError:
            return []
            
    def get_staged_diff(self, max_size: Optional[int] = None) -> str:
        """Get the staged diff."""
        try:
            diff = self._run_git_command(["diff", "--cached", "--no-color"])
            if max_size and len(diff) > max_size:
                diff = diff[:max_size] + "\n\n... (diff truncated)"
            return diff
        except GitError:
            return ""
            
    def get_diff_stats(self) -> str:
        """Get diff statistics."""
        try:
            return self._run_git_command(["diff", "--cached", "--stat", "--no-color"])
        except GitError:
            return ""
            
    def get_recent_commits(self, count: int = 5) -> List[str]:
        """Get recent commit messages for context."""
        try:
            output = self._run_git_command(["log", f"--oneline", f"-{count}", "--no-color"])
            return [line.strip() for line in output.split('\n') if line.strip()]
        except GitError:
            return []
            
    def get_context(self, max_diff_size: int = 8192, include_diff: bool = True) -> Dict[str, Any]:
        """Get comprehensive Git context for AI prompt."""
        context = {
            'branch': self.get_current_branch(),
            'staged_files': self.get_staged_files(),
            'diff_stats': self.get_diff_stats(),
            'recent_commits': self.get_recent_commits(),
        }
        
        if include_diff:
            context['diff'] = self.get_staged_diff(max_diff_size)
        
        return context
        
    def commit(self, message: str) -> str:
        """Create a commit with the given message."""
        # Create temporary file for commit message
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(message)
            commit_file = f.name
            
        try:
            self._run_git_command(["commit", "-F", commit_file])
            # Get the commit hash
            return self._run_git_command(["rev-parse", "--short", "HEAD"])
        finally:
            # Clean up temp file
            try:
                os.unlink(commit_file)
            except OSError:
                pass
                
    def push(self, remote: str, branch: str) -> None:
        """Push to remote repository."""
        self._run_git_command(["push", remote, branch], timeout=60)