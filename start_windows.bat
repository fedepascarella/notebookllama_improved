@echo off
echo ========================================
echo   NotebookLlama Enhanced - Windows Startup
echo ========================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [1/5] Starting Docker services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start Docker services
    pause
    exit /b 1
)

echo.
echo [2/5] Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul

REM Check PostgreSQL connection
docker exec notebookllama-enhanced-postgres-1 pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL might not be fully ready yet
    echo Waiting additional 5 seconds...
    timeout /t 5 /nobreak >nul
)

echo.
echo [3/5] Activating Python virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found!
    echo Creating new virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [4/5] Checking environment variables...
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please create .env file with your API keys
    echo Copy .env.example to .env and update the values
    pause
    exit /b 1
)

echo.
echo [5/5] Starting Streamlit application...
echo.
echo ========================================
echo   Services Status:
echo ========================================
docker-compose ps
echo.
echo ========================================
echo   Application URLs:
echo ========================================
echo   Main App:     http://localhost:8501
echo   Database UI:  http://localhost:8080
echo   Jaeger:       http://localhost:16686
echo ========================================
echo.
echo Starting application in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start Streamlit
streamlit run src/notebookllama/Enhanced_Home.py

echo.
echo Application stopped.
echo.
echo Would you like to stop Docker services? (Y/N)
set /p stop_docker=
if /i "%stop_docker%"=="Y" (
    echo Stopping Docker services...
    docker-compose stop
    echo Docker services stopped.
)

pause