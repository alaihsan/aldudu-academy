@echo off
REM Aldudu Academy - Development Server Runner
REM This script ensures the app runs with the correct virtual environment

echo ===========================================
echo Aldudu Academy - Development Server
echo ===========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    exit /b 1
)

REM Verify we're using the correct Python
echo.
echo Using Python: %PYTHONHOME%
echo.

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Copying from .env copy.example...
    copy ".env copy.example" .env
    echo.
    echo IMPORTANT: Please edit .env with your configuration before running the app
    echo Especially set these variables:
    echo   - DATABASE_URL
    echo   - SECRET_KEY (minimum 32 characters)
    echo   - CELERY_BROKER_URL
    echo.
    pause
    exit /b 1
)

REM Run database migrations
echo Checking database migrations...
flask db upgrade
if errorlevel 1 (
    echo.
    echo WARNING: Migration failed. You may need to run migrations manually.
    echo.
)

echo.
echo ===========================================
echo Starting Flask Development Server
echo ===========================================
echo.
echo Access the application at: http://localhost:5000
echo.
echo Teacher login: guru@aldudu.com / 123
echo Student login: murid@aldudu.com / 123
echo.
echo Press Ctrl+C to stop the server
echo ===========================================
echo.

REM Run the application
flask run
