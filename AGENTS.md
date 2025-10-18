# AGENT CODING GUIDELINES

This document outlines the conventions and commands for agentic development.

## 1. Commands

| Area | Action | Command | Single Test |
| :--- | :--- | :--- | :--- |
| **Backend** | Test | `pytest` | `pytest path/to/test_file.py` |
| **Backend** | Lint/Format | `black . && isort . && flake8 .` | N/A |
| **Frontend** | Build | `npm run build` | N/A |
| **Frontend** | Test | `npm run test` | `npm run test -- path/to/test_file.tsx` |
| **Frontend** | Lint/Format | `npm run lint:fix && npm run format` | N/A |

## 2. Style & Conventions

### Python (Backend)
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes.
- **Typing:** Fully typed; enforce with `mypy --strict`.
- **API:** Use `HTTPException` for error handling in FastAPI endpoints.
- **Formatting:** Strict `black` (line-length 88) and `isort` compliance.

### TypeScript/React (Frontend)
- **Naming:** `camelCase` for functions/variables, `PascalCase` for components/types.
- **Styling:** Use **Tailwind CSS only**.
- **Typing:** Strong TypeScript typing; avoid `@typescript-eslint/no-explicit-any`.
- **React:** Use functional components and hooks.

## 3. General Rules
- **Code:** No comments in code. Achieve functionality with minimum code.
- **Commits:** Commit frequently. Do not push without instruction.
- **File Deletion:** Move deleted files to the recycle bin (do not permanently delete).
- **Restart:** Inform the user if a restart is required to see changes.
