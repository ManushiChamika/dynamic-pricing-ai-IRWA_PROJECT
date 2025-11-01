"""OpenCode AI provider for commit message generation."""

import subprocess
import json
import shutil
from typing import Optional, Dict, Any
import re


class OpenCodeError(Exception):
    """Raised when OpenCode operations fail."""
    pass


class OpenCodeProvider:
    """OpenCode AI provider for generating commit messages."""
    
    def __init__(self, model: Optional[str] = None, agent: Optional[str] = None, verbose: bool = False):
        """Initialize OpenCode provider."""
        self.model = model
        self.agent = agent
        self.verbose = verbose
        self._validate_opencode()
        
    def _validate_opencode(self) -> None:
        """Ensure OpenCode CLI is available and working."""
        # Check if opencode is in PATH
        if not shutil.which("opencode"):
            raise OpenCodeError(
                "OpenCode CLI not found. Please ensure 'opencode' is installed and in your PATH.\n"
                "Visit: https://github.com/sst/opencode for installation instructions."
            )
            
        # Test that opencode responds
        try:
            result = subprocess.run(
                ["opencode", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise OpenCodeError(f"OpenCode CLI check failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise OpenCodeError("OpenCode CLI is not responding")
        except FileNotFoundError:
            raise OpenCodeError("OpenCode CLI not found")
            
    def _build_opencode_command(self, prompt: str) -> list[str]:
        """Build OpenCode command with appropriate flags."""
        cmd = ["opencode", "run"]
        
        # Add model if specified
        if self.model:
            cmd.extend(["--model", self.model])
            
        # Add agent if specified
        if self.agent:
            cmd.extend(["--agent", self.agent])
            
        # Use JSON format for better parsing
        cmd.extend(["--format", "json"])
        
        # Add the prompt as positional argument
        cmd.append(prompt)
        
        return cmd
        
    def _parse_opencode_output(self, output: str) -> str:
        """Parse OpenCode JSON output to extract the commit message."""
        if not output.strip():
            raise OpenCodeError("OpenCode returned empty output")
            
        # OpenCode returns JSON events, we need to extract the assistant messages
        messages = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                event = json.loads(line)
                
                # Look for assistant text content
                if (event.get('type') == 'text' and 
                    event.get('role') == 'assistant' and 
                    event.get('content')):
                    messages.append(event['content'])
                    
            except json.JSONDecodeError:
                # Skip non-JSON lines (might be debug output)
                continue
                
        if not messages:
            # Try to parse as single JSON object
            try:
                data = json.loads(output)
                if isinstance(data, dict) and 'content' in data:
                    messages.append(data['content'])
                elif isinstance(data, str):
                    messages.append(data)
            except json.JSONDecodeError:
                # Last resort: treat as plain text if it looks like a commit message
                if self._looks_like_commit_message(output):
                    return output.strip()
                    
                raise OpenCodeError(f"Unable to parse OpenCode output: {output[:200]}...")
                
        if not messages:
            raise OpenCodeError("No commit message found in OpenCode output")
            
        # Join all message parts
        full_message = ''.join(messages).strip()
        
        if not full_message:
            raise OpenCodeError("OpenCode returned empty commit message")
            
        return full_message
        
    def _looks_like_commit_message(self, text: str) -> bool:
        """Check if text looks like a commit message."""
        text = text.strip()
        if not text:
            return False
            
        # Check for conventional commit pattern
        conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore|ci|perf)(\([^)]+\))?: .+'
        if re.match(conventional_pattern, text):
            return True
            
        # Check for help text patterns (should be rejected)
        help_patterns = [
            "opencode run",
            "usage:",
            "options:",
            "positionals:",
            "--help",
            "Commands:",
        ]
        
        text_lower = text.lower()
        for pattern in help_patterns:
            if pattern in text_lower:
                return False
                
        return True
        
    def _clean_commit_message(self, message: str) -> str:
        """Clean and normalize the commit message."""
        # Remove any markdown formatting
        message = re.sub(r'```[^`]*```', '', message)  # Remove code blocks
        message = re.sub(r'`([^`]+)`', r'\1', message)  # Remove inline code
        message = re.sub(r'\*\*([^*]+)\*\*', r'\1', message)  # Remove bold
        message = re.sub(r'\*([^*]+)\*', r'\1', message)  # Remove italic
        
        # Remove any extra whitespace and normalize line endings
        lines = [line.rstrip() for line in message.split('\n')]
        message = '\n'.join(lines).strip()
        
        # Ensure proper line wrapping (72 chars for body)
        lines = message.split('\n')
        if len(lines) > 1:
            # Keep first line (subject) as-is, wrap body lines
            wrapped_lines = [lines[0]]
            for line in lines[1:]:
                if len(line) > 72:
                    # Simple word wrap
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= 72:
                            current_line += (" " + word) if current_line else word
                        else:
                            if current_line:
                                wrapped_lines.append(current_line)
                            current_line = word
                    if current_line:
                        wrapped_lines.append(current_line)
                else:
                    wrapped_lines.append(line)
            message = '\n'.join(wrapped_lines)
            
        return message
        
    def generate_commit_message(self, prompt: str) -> str:
        """Generate commit message using OpenCode."""
        if self.verbose:
            print("[DEBUG] Calling OpenCode...")
            
        cmd = self._build_opencode_command(prompt)
        
        try:
            if self.verbose:
                print(f"[DEBUG] Running: {' '.join(cmd[:3])} [prompt]")
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "not found" in error_msg.lower():
                    raise OpenCodeError("OpenCode CLI not found or not executable")
                elif "timeout" in error_msg.lower():
                    raise OpenCodeError("OpenCode request timed out")
                else:
                    raise OpenCodeError(f"OpenCode failed: {error_msg}")
                    
            if self.verbose:
                print(f"[DEBUG] OpenCode raw output length: {len(result.stdout)} chars")
                
            # Parse and clean the output
            message = self._parse_opencode_output(result.stdout)
            message = self._clean_commit_message(message)
            
            if not message:
                raise OpenCodeError("OpenCode returned empty commit message after cleaning")
                
            if self.verbose:
                print(f"[DEBUG] Generated message length: {len(message)} chars")
                
            return message
            
        except subprocess.TimeoutExpired:
            raise OpenCodeError("OpenCode request timed out (120s limit)")
        except FileNotFoundError:
            raise OpenCodeError("OpenCode CLI not found")
        except Exception as e:
            if isinstance(e, OpenCodeError):
                raise
            raise OpenCodeError(f"Unexpected error calling OpenCode: {e}")