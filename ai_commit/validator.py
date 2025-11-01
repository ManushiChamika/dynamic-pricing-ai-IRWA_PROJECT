"""Conventional commit message validator."""

import re
from typing import List, Optional


class ValidationError(Exception):
    """Raised when commit message validation fails."""
    pass


class CommitMessageValidator:
    """Validates commit messages against conventional commit standards."""
    
    # Valid conventional commit types
    VALID_TYPES = {
        'feat', 'fix', 'docs', 'style', 'refactor', 
        'test', 'chore', 'ci', 'perf', 'build', 'revert'
    }
    
    # Maximum lengths
    MAX_SUBJECT_LENGTH = 50
    MAX_BODY_LINE_LENGTH = 72
    
    def __init__(self):
        """Initialize validator."""
        # Pattern for conventional commit header
        self.header_pattern = re.compile(
            r'^(?P<type>\w+)'          # type
            r'(?:\((?P<scope>[^)]+)\))?' # optional scope
            r'(?P<breaking>!)?' # optional breaking change marker
            r': '                      # separator
            r'(?P<subject>.+)$'        # subject
        )
        
    def validate(self, message: str) -> None:
        """Validate a commit message."""
        if not message or not message.strip():
            raise ValidationError("Commit message cannot be empty")
            
        lines = message.strip().split('\n')
        
        # Validate header (first line)
        self._validate_header(lines[0])
        
        # Validate body if present
        if len(lines) > 1:
            self._validate_body(lines[1:])
            
    def _validate_header(self, header: str) -> None:
        """Validate the commit message header."""
        if not header:
            raise ValidationError("Commit message header cannot be empty")
            
        # Check length
        if len(header) > self.MAX_SUBJECT_LENGTH:
            raise ValidationError(
                f"Header too long ({len(header)} chars). "
                f"Maximum {self.MAX_SUBJECT_LENGTH} characters allowed."
            )
            
        # Check conventional commit format
        match = self.header_pattern.match(header)
        if not match:
            raise ValidationError(
                "Header must follow conventional commit format: "
                "type(scope): subject"
            )
            
        commit_type = match.group('type')
        subject = match.group('subject')
        
        # Validate type
        if commit_type not in self.VALID_TYPES:
            raise ValidationError(
                f"Invalid commit type '{commit_type}'. "
                f"Valid types: {', '.join(sorted(self.VALID_TYPES))}"
            )
            
        # Validate subject
        if not subject or not subject.strip():
            raise ValidationError("Subject cannot be empty")
            
        if subject[0].isupper():
            raise ValidationError("Subject should not start with uppercase letter")
            
        if subject.endswith('.'):
            raise ValidationError("Subject should not end with period")
            
    def _validate_body(self, body_lines: List[str]) -> None:
        """Validate the commit message body."""
        # Skip empty line after header (conventional)
        if body_lines and body_lines[0].strip() == '':
            body_lines = body_lines[1:]
            
        for i, line in enumerate(body_lines, 2):  # Start line count at 2
            if len(line) > self.MAX_BODY_LINE_LENGTH:
                raise ValidationError(
                    f"Line {i} too long ({len(line)} chars). "
                    f"Maximum {self.MAX_BODY_LINE_LENGTH} characters allowed."
                )
                
    def get_header_info(self, message: str) -> Optional[dict]:
        """Extract header information from commit message."""
        lines = message.strip().split('\n')
        if not lines:
            return None
            
        match = self.header_pattern.match(lines[0])
        if not match:
            return None
            
        return {
            'type': match.group('type'),
            'scope': match.group('scope'),
            'breaking': bool(match.group('breaking')),
            'subject': match.group('subject')
        }
        
    def format_message(self, commit_type: str, subject: str, 
                      scope: Optional[str] = None, 
                      body: Optional[str] = None,
                      breaking: bool = False) -> str:
        """Format a conventional commit message."""
        # Build header
        header = commit_type
        if scope:
            header += f"({scope})"
        if breaking:
            header += "!"
        header += f": {subject}"
        
        # Validate header length
        if len(header) > self.MAX_SUBJECT_LENGTH:
            raise ValidationError(f"Formatted header too long: {len(header)} chars")
            
        # Build full message
        message = header
        if body:
            message += "\n\n" + body
            
        return message