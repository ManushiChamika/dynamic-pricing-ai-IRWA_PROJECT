@echo off
echo ============================================
echo Running LLM Refactoring Test Suite
echo ============================================
echo.

echo [1/3] Running comprehensive LLM client tests...
pytest test_llm_comprehensive.py -v -s
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: LLM client tests failed
    exit /b 1
)

echo.
echo [2/3] Running LLM integration tests...
pytest test_llm_integration.py -v -s
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: LLM integration tests failed
    exit /b 1
)

echo.
echo [3/3] Running existing provider verification test...
pytest test_llm_provider_verification.py -v -s
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Provider verification test failed
    exit /b 1
)

echo.
echo ============================================
echo All LLM tests passed successfully!
echo ============================================
