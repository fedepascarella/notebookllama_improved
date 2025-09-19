@echo off
echo =============================================
echo  Enhanced Workflow V2 - API Key Setup
echo =============================================
echo.

echo This script will help you set up your OpenAI API key.
echo.

set /p api_key="Enter your OpenAI API key: "

if "%api_key%"=="" (
    echo No API key entered. Exiting...
    pause
    exit /b 1
)

echo.
echo Setting OPENAI_API_KEY environment variable...
setx OPENAI_API_KEY "%api_key%"

echo.
echo API key has been set!
echo Note: You may need to restart your command prompt for the change to take effect.
echo.
echo You can now run: launch_enhanced_workflow_v2.bat
echo.
pause