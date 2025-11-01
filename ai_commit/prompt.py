"""Prompt builder for AI commit message generation."""

from typing import Dict, Any, List


class PromptBuilder:
    """Builds prompts for AI commit message generation."""
    
    def __init__(self):
        """Initialize prompt builder."""
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt with rules and format."""
        return """You are a Git commit message generator. Create a conventional commit message from the provided Git context.

REQUIREMENTS:
- Use format: <type>(<scope>): <subject>
- Subject maximum 50 characters
- Subject should be lowercase and not end with period
- Include detailed body explaining WHY and WHAT changed
- Body wrapped at 72 characters per line
- Leave blank line between subject and body
- No code blocks, markdown formatting, or extra explanations
- Output ONLY the commit message text

TYPES: feat, fix, docs, style, refactor, test, chore, ci, perf, build, revert

SCOPE GUIDELINES:
- Use component/module names when applicable
- Examples: api, ui, core, config, tooling, deps
- Omit scope if change affects entire project

EXAMPLES:
feat(api): add user authentication endpoint

Implement JWT-based authentication system with login and logout
endpoints. Includes middleware for token validation and user
session management.

fix(ui): resolve button alignment in mobile view

Corrected CSS flexbox properties causing misaligned buttons on
screens smaller than 768px. Updated responsive design to ensure
consistent layout across all device sizes.

chore(deps): update development dependencies

Updated ESLint to v8.45.0 and Prettier to v3.0.1 for improved
code formatting and linting capabilities. No breaking changes
in existing codebase."""
        
    def _redact_sensitive_data(self, text: str) -> str:
        """Remove potentially sensitive information from text."""
        import re
        
        # Common patterns to redact
        patterns = [
            (r'password\s*=\s*["\']?[^"\'\s]+["\']?', 'password=***'),
            (r'api[_-]?key\s*=\s*["\']?[^"\'\s]+["\']?', 'api_key=***'),
            (r'secret\s*=\s*["\']?[^"\'\s]+["\']?', 'secret=***'),
            (r'token\s*=\s*["\']?[^"\'\s]+["\']?', 'token=***'),
            (r'(?i)bearer\s+[a-zA-Z0-9._-]+', 'bearer ***'),
            (r'(?i)authorization:\s*[^\r\n]+', 'authorization: ***'),
        ]
        
        redacted = text
        for pattern, replacement in patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
            
        return redacted
        
    def _format_file_changes(self, staged_files: List[tuple[str, str]]) -> str:
        """Format staged file changes for prompt."""
        if not staged_files:
            return "No files changed"
            
        # Group by change type
        changes = {'A': [], 'M': [], 'D': [], 'R': [], 'C': []}
        for status, filename in staged_files:
            if status in changes:
                changes[status].append(filename)
            else:
                changes.setdefault('Other', []).append(f"{status} {filename}")
                
        lines = []
        if changes['A']:
            lines.append(f"Added: {', '.join(changes['A'])}")
        if changes['M']:
            lines.append(f"Modified: {', '.join(changes['M'])}")
        if changes['D']:
            lines.append(f"Deleted: {', '.join(changes['D'])}")
        if changes['R']:
            lines.append(f"Renamed: {', '.join(changes['R'])}")
        if changes['C']:
            lines.append(f"Copied: {', '.join(changes['C'])}")
        if changes.get('Other'):
            lines.extend(changes['Other'])
            
        return '\n'.join(lines)
        
    def _analyze_change_patterns(self, staged_files: List[tuple[str, str]]) -> Dict[str, Any]:
        """Analyze file patterns to suggest commit type and scope."""
        analysis = {
            'suggested_type': 'chore',
            'suggested_scope': None,
            'has_tests': False,
            'has_docs': False,
            'has_config': False,
            'has_new_files': False,
            'has_deleted_files': False,
        }
        
        test_patterns = ['test', 'spec', '__tests__', '.test.', '.spec.']
        doc_patterns = ['.md', 'readme', 'doc/', 'docs/']
        config_patterns = ['config', '.json', '.yaml', '.yml', '.toml', '.ini', 'requirements']
        
        for status, filename in staged_files:
            filename_lower = filename.lower()
            
            # Check file type patterns
            if any(pattern in filename_lower for pattern in test_patterns):
                analysis['has_tests'] = True
                
            if any(pattern in filename_lower for pattern in doc_patterns):
                analysis['has_docs'] = True
                
            if any(pattern in filename_lower for pattern in config_patterns):
                analysis['has_config'] = True
                
            # Check change types
            if status == 'A':
                analysis['has_new_files'] = True
            elif status == 'D':
                analysis['has_deleted_files'] = True
                
        # Suggest commit type based on patterns
        if analysis['has_tests'] and not analysis['has_docs'] and not analysis['has_config']:
            analysis['suggested_type'] = 'test'
        elif analysis['has_docs'] and not analysis['has_config']:
            analysis['suggested_type'] = 'docs'
        elif analysis['has_new_files'] and not analysis['has_tests']:
            analysis['suggested_type'] = 'feat'
        elif analysis['has_config']:
            analysis['suggested_type'] = 'chore'
            analysis['suggested_scope'] = 'config'
            
        return analysis
        
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """Build complete prompt from Git context."""
        # Extract context data
        branch = context.get('branch', 'unknown')
        staged_files = context.get('staged_files', [])
        diff_stats = context.get('diff_stats', '')
        recent_commits = context.get('recent_commits', [])
        diff = context.get('diff', '')
        
        # Analyze patterns
        analysis = self._analyze_change_patterns(staged_files)
        
        # Build context sections
        sections = [
            self.system_prompt,
            "",
            f"Current branch: {branch}",
            "",
            "=== CHANGED FILES ===",
            self._format_file_changes(staged_files),
        ]
        
        if diff_stats:
            sections.extend([
                "",
                "=== CHANGE STATISTICS ===",
                diff_stats,
            ])
            
        if recent_commits:
            sections.extend([
                "",
                "=== RECENT COMMITS (for context) ===",
                '\n'.join(recent_commits[:3]),  # Limit to 3 most recent
            ])
            
        # Add suggestions based on analysis
        if analysis['suggested_type'] != 'chore':
            sections.extend([
                "",
                f"=== ANALYSIS HINTS ===",
                f"Suggested type: {analysis['suggested_type']}",
            ])
            if analysis['suggested_scope']:
                sections.append(f"Suggested scope: {analysis['suggested_scope']}")
                
        # Add diff if provided
        if diff:
            sections.extend([
                "",
                "=== DIFF CONTENT ===",
                self._redact_sensitive_data(diff),
            ])
            
        return '\n'.join(sections)