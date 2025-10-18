# Agent Instructions

Monorepo with Python/FastAPI backend and TypeScript/React frontend. Backend in backend/, frontend in frontend/.

## Backend (Python)

*Run:* using "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\run_full_app.bat"

*Test:* pytest (all), pytest path/to/test_file.py (single)
*Lint:* black ., isort ., flake8 . before committing
*Style:* snake_case functions/vars, PascalCase classes; fully typed (mypy strict); use HTTPException in API endpoints

## Frontend (TypeScript/React)

*Run:* "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\run_full_app.bat"
*Build:* npm run build
*Test:* npm run test (all), npm run test -- path/to/test_file.tsx (single)
*Lint/Format:* npm run lint:fix, npm run format before committing
*Style:* camelCase functions/vars, PascalCase components/types; Tailwind CSS only; strong TypeScript typing

## Important

- when you want to use chrome mcp tools do not attempt to run the backend and the frontend yourself just ask the user to run the full app and provide the necessary details
- No comments in code
- Try to achieve the desired functionality with minimum code
- Testing credentials: demo@example.com / 1234567890
-  Important : when you delete files move them to recycle bin do not permanently delete.  
-  Commit frequently . do not push without instruction . commit super frequently 
- i am new to git when you do something intermediate or advanced inform me what is happening 
- If you made a change then tell me weather i have to restart to see the changes