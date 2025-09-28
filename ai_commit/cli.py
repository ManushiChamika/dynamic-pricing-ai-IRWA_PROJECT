#!/usr/bin/env python3
"""Main CLI entry point for ai-commit."""

import argparse
import sys
import os

from typing import Optional, List, Tuple

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


def _build_fallback_message(context: dict) -> str:
    """Build a conventional commit message without AI as a fallback.

    Keeps lines under 72 chars in the body and avoids long file listings.
    """
    staged_files: List[Tuple[str, str]] = context.get('staged_files', [])

    has_new = any(s == 'A' for s, _ in staged_files)
    has_mod = any(s == 'M' for s, _ in staged_files)
    has_del = any(s == 'D' for s, _ in staged_files)

    def any_match(substrs: List[str], name: str) -> bool:
        name_l = name.lower()
        return any(sub in name_l for sub in substrs)

    has_tests = any(any_match(['test', '.test.', '_test', '__tests__', 'spec'], f) for _, f in staged_files)
    has_docs = any(any_match(['.md', 'readme', 'docs/'], f) for _, f in staged_files)
    has_config = any(any_match(['config', '.json', '.yaml', '.yml', '.toml', '.ini', 'requirements'], f) for _, f in staged_files)
    has_scripts = any(any_match(['script', '.bat', '.ps1', '.sh'], f) for _, f in staged_files)
    has_ui = any(any_match(['ui', 'frontend', 'component'], f) for _, f in staged_files)
    has_core = any(any_match(['core', 'agent', 'backend'], f) for _, f in staged_files)

    commit_type = 'chore'
    scope: Optional[str] = None

    if has_tests and not (has_docs or has_config):
        commit_type = 'test'
    elif has_docs and not has_config:
        commit_type = 'docs'
    elif has_new and not has_tests:
        commit_type = 'feat'
    elif has_config:
        commit_type = 'chore'
        scope = 'config'

    if has_scripts:
        commit_type = 'feat'
        scope = (scope or 'tooling')

    if has_ui:
        scope = scope or 'ui'
    if has_core:
        scope = scope or 'core'

    if commit_type == 'docs':
        subject = 'update documentation'
    elif commit_type == 'test':
        subject = 'update test coverage'
    elif commit_type == 'chore' and scope == 'config':
        subject = 'update configuration'
    elif commit_type == 'feat' and scope == 'tooling':
        subject = 'enhance development tooling'
    elif has_new and not (has_mod or has_del):
        subject = 'add new components'
    else:
        subject = 'update project components'

    # Summarize counts to keep body concise
    count_a = sum(1 for s, _ in staged_files if s == 'A')
    count_m = sum(1 for s, _ in staged_files if s == 'M')
    count_d = sum(1 for s, _ in staged_files if s == 'D')

    bullet_lines: List[str] = [
        'Changes include:'
    ]
    if count_a:
        bullet_lines.append(f"- added {count_a} file{'s' if count_a != 1 else ''}")
    if count_m:
        bullet_lines.append(f"- modified {count_m} file{'s' if count_m != 1 else ''}")
    if count_d:
        bullet_lines.append(f"- removed {count_d} file{'s' if count_d != 1 else ''}")
    if has_tests:
        bullet_lines.append("- updated tests")
    if has_docs:
        bullet_lines.append("- updated docs")
    if has_config:
        bullet_lines.append("- configuration adjustments")
    if has_scripts:
        bullet_lines.append("- tooling updates")

    bullet_lines.append(
        f"summary: {count_a} added, {count_m} modified, {count_d} deleted"
    )

    body = "\n".join(bullet_lines)

    validator = CommitMessageValidator()
    message = validator.format_message(commit_type, subject, scope=scope, body=body)
    # Validate to ensure it conforms
    validator.validate(message)
    return message


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
        
        try:
            message = provider.generate_commit_message(prompt)
        except OpenCodeError as e:
            if args.verbose:
                print(f"[WARN] OpenCode generation failed: {e}")
                print("[INFO] Falling back to local conventional commit generator...")
            message = _build_fallback_message(context)
        
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
        # This would only be hit during provider init/validation
        if args.verbose:
            print(f"[WARN] OpenCode unavailable during initialization: {e}")
            print("[INFO] Falling back to local conventional commit generator...")
        try:
            message = _build_fallback_message({'staged_files': []})
            print(message)
            return 0 if args.dry_run else 1
        except Exception as inner:
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
