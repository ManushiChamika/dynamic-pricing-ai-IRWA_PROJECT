"""Test validator module."""

import pytest
from ai_commit.validator import CommitMessageValidator, ValidationError


class TestCommitMessageValidator:
    """Test cases for CommitMessageValidator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = CommitMessageValidator()
        
    def test_valid_conventional_commit(self):
        """Test valid conventional commit message."""
        message = "feat(api): add user authentication"
        # Should not raise
        self.validator.validate(message)
        
    def test_valid_commit_with_body(self):
        """Test valid commit with body."""
        message = """feat(api): add user authentication

Implement JWT-based authentication system with login and logout
endpoints. Includes middleware for token validation."""
        # Should not raise
        self.validator.validate(message)
        
    def test_empty_message(self):
        """Test empty message validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            self.validator.validate("")
            
    def test_invalid_type(self):
        """Test invalid commit type."""
        message = "invalid: add something"
        with pytest.raises(ValidationError, match="Invalid commit type"):
            self.validator.validate(message)
            
    def test_subject_too_long(self):
        """Test subject length validation."""
        message = "feat: " + "a" * 50  # Over 50 chars total
        with pytest.raises(ValidationError, match="Header too long"):
            self.validator.validate(message)
            
    def test_subject_uppercase_start(self):
        """Test subject should not start with uppercase."""
        message = "feat: Add new feature"
        with pytest.raises(ValidationError, match="should not start with uppercase"):
            self.validator.validate(message)
            
    def test_subject_ends_with_period(self):
        """Test subject should not end with period."""
        message = "feat: add new feature."
        with pytest.raises(ValidationError, match="should not end with period"):
            self.validator.validate(message)
            
    def test_body_line_too_long(self):
        """Test body line length validation."""
        message = f"""feat: add feature

This is a very long line that exceeds the maximum allowed length for body text in conventional commits which should be wrapped at 72 characters maximum."""
        with pytest.raises(ValidationError, match="Line .+ too long"):
            self.validator.validate(message)
            
    def test_get_header_info(self):
        """Test header info extraction."""
        message = "feat(api): add authentication"
        info = self.validator.get_header_info(message)
        
        assert info is not None
        assert info['type'] == 'feat'
        assert info['scope'] == 'api'
        assert info['subject'] == 'add authentication'
        assert info['breaking'] is False
        
    def test_get_header_info_with_breaking(self):
        """Test header info extraction with breaking change."""
        message = "feat!: major api change"
        info = self.validator.get_header_info(message)
        
        assert info is not None
        assert info['type'] == 'feat'
        assert info['scope'] is None
        assert info['subject'] == 'major api change'
        assert info['breaking'] is True
        
    def test_format_message(self):
        """Test message formatting."""
        message = self.validator.format_message(
            'feat', 'add new feature', scope='api', 
            body='Detailed explanation'
        )
        
        expected = """feat(api): add new feature

Detailed explanation"""
        assert message == expected