# AI-Commit: AI-Powered Git Commit Message Generator

An intelligent Git commit message generator that uses OpenCode AI to create conventional commit messages based on your staged changes.

## Features

- **OpenCode Integration**: Uses OpenCode CLI for AI-powered commit message generation
- **Conventional Commits**: Enforces conventional commit format with proper validation
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Smart Analysis**: Analyzes file changes and Git context for intelligent suggestions
- **Privacy-Aware**: Handles sensitive data carefully in diffs
- **Flexible Usage**: Supports dry-run, auto-commit, and push options

## Installation

```bash
# Install in development mode
pip install -e .

# This creates the `ai-commit` command globally
```

## Prerequisites

- Python 3.8+
- Git repository
- [OpenCode CLI](https://github.com/sst/opencode) installed and configured

## Usage

### Basic Usage

```bash
# Interactive mode - asks for confirmation
ai-commit

# Or using Python module directly
python -m ai_commit.cli
```

### Command Options

```bash
# Auto-commit without confirmation
ai-commit --yes

# Dry run - show message without committing
ai-commit --dry-run

# Commit and push to remote
ai-commit --push

# Use specific model or agent
ai-commit --model claude --agent coding

# Verbose output for debugging
ai-commit --verbose

# Limit diff size for large changes
ai-commit --max-diff-size 4000

# Skip diff in prompt (only file lists)
ai-commit --no-diff
```

### Example Workflow

```bash
# Make your changes
git add .

# Generate and commit with AI
ai-commit --dry-run    # Review the message first
ai-commit --yes        # Auto-commit if satisfied
```

## How It Works

1. **Context Gathering**: Analyzes your staged changes and Git history
2. **Prompt Building**: Creates an intelligent prompt with file changes and context
3. **AI Generation**: Uses OpenCode to generate a conventional commit message
4. **Validation**: Ensures the message follows conventional commit standards
5. **Commit**: Creates the commit with the generated message

## Configuration

The tool automatically detects:
- Staged files and their changes
- Recent commit history for context
- File patterns to suggest appropriate commit types and scopes

## Commit Message Format

Generated messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Supported types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `perf`: Performance improvements

## Error Handling

The tool handles various scenarios:
- No staged changes (auto-stages all changes)
- Merge conflicts (prompts to resolve first)
- OpenCode API errors (clear error messages)
- Invalid commit messages (validation feedback)

## Development

### Project Structure

```
ai_commit/
├── __init__.py          # Package initialization
├── cli.py               # Main CLI entry point
├── git_context.py       # Git operations and context gathering  
├── prompt.py            # AI prompt building logic
├── validator.py         # Commit message validation
└── providers/
    ├── __init__.py
    └── opencode.py      # OpenCode API integration
```

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=ai_commit
```

### Testing Components

```bash
# Test all components
python test_core_workflow.py

# Test specific modules
python -c "from ai_commit.git_context import GitContext; print('Git context works!')"
```

## Troubleshooting

### Common Issues

1. **OpenCode not found**
   ```bash
   # Install OpenCode CLI
   npm install -g @opencode/cli
   # Or follow installation guide at https://github.com/sst/opencode
   ```

2. **No staged changes**
   ```bash
   git add .  # Stage your changes first
   ```

3. **Merge conflicts**
   ```bash
   git status  # Check for conflicts
   # Resolve conflicts, then try again
   ```

4. **Unicode errors on Windows**
   ```bash
   # Set console to UTF-8
   chcp 65001
   ```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Note**: This tool requires an active internet connection and OpenCode API access for AI message generation.