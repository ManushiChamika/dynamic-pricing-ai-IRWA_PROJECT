"""Test OpenCode provider."""

import json
import subprocess
from unittest.mock import Mock, patch
import pytest

from ai_commit.providers.opencode import OpenCodeProvider, OpenCodeError


class TestOpenCodeProvider:
    """Test cases for OpenCodeProvider."""
    
    def test_init_validates_opencode(self):
        """Test that initialization validates OpenCode availability."""
        with patch('shutil.which', return_value=None):
            with pytest.raises(OpenCodeError, match="not found"):
                OpenCodeProvider()
                
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_successful_message_generation(self, mock_run, mock_which):
        """Test successful commit message generation."""
        mock_which.return_value = '/usr/bin/opencode'
        
        # Mock version check
        version_result = Mock()
        version_result.returncode = 0
        
        # Mock actual generation
        generate_result = Mock()
        generate_result.returncode = 0
        generate_result.stdout = json.dumps({
            "type": "text",
            "role": "assistant", 
            "content": "feat(api): add user authentication\n\nImplement JWT-based auth system"
        })
        
        mock_run.side_effect = [version_result, generate_result]
        
        provider = OpenCodeProvider()
        message = provider.generate_commit_message("test prompt")
        
        assert "feat(api): add user authentication" in message
        assert "JWT-based auth system" in message
        
    @patch('shutil.which')
    @patch('subprocess.run') 
    def test_empty_output_handling(self, mock_run, mock_which):
        """Test handling of empty OpenCode output."""
        mock_which.return_value = '/usr/bin/opencode'
        
        version_result = Mock()
        version_result.returncode = 0
        
        generate_result = Mock()
        generate_result.returncode = 0
        generate_result.stdout = ""
        
        mock_run.side_effect = [version_result, generate_result]
        
        provider = OpenCodeProvider()
        with pytest.raises(OpenCodeError, match="empty output"):
            provider.generate_commit_message("test prompt")
            
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_opencode_failure(self, mock_run, mock_which):
        """Test handling of OpenCode command failure."""
        mock_which.return_value = '/usr/bin/opencode'
        
        version_result = Mock()
        version_result.returncode = 0
        
        generate_result = Mock()
        generate_result.returncode = 1
        generate_result.stderr = "OpenCode error"
        
        mock_run.side_effect = [version_result, generate_result]
        
        provider = OpenCodeProvider()
        with pytest.raises(OpenCodeError, match="OpenCode failed"):
            provider.generate_commit_message("test prompt")
            
    def test_looks_like_commit_message(self):
        """Test commit message detection."""
        provider = OpenCodeProvider.__new__(OpenCodeProvider)  # Skip __init__
        
        # Valid commit messages
        assert provider._looks_like_commit_message("feat: add new feature")
        assert provider._looks_like_commit_message("fix(ui): resolve button issue")
        
        # Invalid (help text)
        assert not provider._looks_like_commit_message("opencode run [message..]")
        assert not provider._looks_like_commit_message("Usage: opencode")
        assert not provider._looks_like_commit_message("")