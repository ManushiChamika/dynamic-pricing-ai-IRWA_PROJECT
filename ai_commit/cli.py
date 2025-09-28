#!/usr/bin/env python3
"""Main CLI entry point for ai-commit."""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Handle both relative and absolute imports
try:
    from .git_context import GitContext, GitError
    from .providers.opencode import OpenCodeProvider, OpenCodeError
    from .validator import CommitMessageValidator, ValidationError
    from .prompt import PromptBuilder
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from git_context import GitContext, GitError
    from providers.opencode import OpenCodeProvider, OpenCodeError
    from validator import CommitMessageValidator, ValidationError
    from prompt import PromptBuilder


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AI-powered Git commit message generator using OpenCode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-commit                    # Interactive commit with AI-generated message
  ai-commit --yes              # Auto-commit without confirmation
  ai-commit --dry-run          # Generate message but don't commit
  ai-commit --push             # Commit and push to origin
  ai-commit --model claude     # Use specific model
        """
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-accept generated commit message without confirmation"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true", 
        help="Generate commit message but don't actually commit"
    )
    
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to remote after successful commit"
    )
    
    parser.add_argument(
        "--remote",
        default="origin",
        help="Remote to push to (default: origin)"
    )
    
    parser.add_argument(
        "--branch",
        help="Branch to push to (default: current branch)"
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Model to use (e.g., claude, gpt-4)"
    )
    
    parser.add_argument(
        "--agent",
        help="Agent to use for generation"
    )
    
    parser.add_argument(
        "--max-diff-size",
        type=int,
        default=8192,
        help="Maximum diff size in characters (default: 8192)"
    )
    
    parser.add_argument(
        "--no-diff",
        action="store_true",
        help="Don't include diff in prompt (only file lists and stats)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser


def confirm_commit(message: str) -> bool:
    """Ask user to confirm the commit message."""
    print("\n" + "=" * 60)
    print("GENERATED COMMIT MESSAGE")  
    print("=" * 60)
    print(message)
    print("=" * 60)
    
    try:
        response = input("\nProceed with this commit message? (y/N): ").strip().lower()
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled by user")
        return False


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Initialize Git context
        if args.verbose:
            print("[INFO] Checking Git repository status...")
        
        git = GitContext()
        
        # Check for changes
        if not git.has_staged_changes():
            if args.verbose:
                print("[INFO] No staged changes found, staging all changes...")
            git.stage_all()
            
        if not git.has_staged_changes():
            print("No changes to commit")
            return 0
            
        # Check for conflicts
        if git.has_conflicts():
            print("ERROR: Merge conflicts detected. Please resolve before committing.")
            return 1
            
        # Gather context
        if args.verbose:
            print("[INFO] Gathering Git context...")
            
        context = git.get_context(
            max_diff_size=args.max_diff_size,
            include_diff=not args.no_diff
        )
        
        # Build prompt
        if args.verbose:
            print("[INFO] Building AI prompt...")
            
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_prompt(context)
        
        # Generate commit message with OpenCode
        if args.verbose:
            print("[INFO] Generating commit message with OpenCode...")
            
        provider = OpenCodeProvider(
            model=args.model,
            agent=args.agent,
            verbose=args.verbose
        )
        
        message = provider.generate_commit_message(prompt)
        
        # Validate message
        if args.verbose:
            print("[INFO] Validating commit message...")
            
        validator = CommitMessageValidator()
        validator.validate(message)
        
        # Dry run - just show the message
        if args.dry_run:
            print("\n" + "=" * 60)
            print("GENERATED COMMIT MESSAGE (DRY RUN)")
            print("=" * 60)
            print(message)
            print("=" * 60)
            return 0
            
        # Confirm with user (unless --yes)
        if not args.yes:
            if not confirm_commit(message):
                print("Commit cancelled")
                return 0
                
        # Commit the changes
        if args.verbose:
            print("[INFO] Creating commit...")
            
        commit_hash = git.commit(message)
        print(f"Commit successful: {commit_hash}")
        
        # Push if requested
        if args.push:
            if args.verbose:
                print(f"[INFO] Pushing to {args.remote}...")
                
            branch = args.branch or git.get_current_branch()
            git.push(args.remote, branch)
            print(f"Successfully pushed to {args.remote}/{branch}")
            
        return 0
        
    except GitError as e:
        print(f"Git error: {e}")
        return 1
    except OpenCodeError as e:
        print(f"OpenCode error: {e}")
        return 1
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())