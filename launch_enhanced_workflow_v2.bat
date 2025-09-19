@echo off
echo ============================================
echo  Enhanced Workflow V2 - Senior Level Launch
echo ============================================
echo.

REM Check if OpenAI API key is set
if "%OPENAI_API_KEY%"=="" (
    echo WARNING: OPENAI_API_KEY environment variable not set!
    echo Please set it with: set OPENAI_API_KEY=your-api-key-here
    echo.
    echo The application will still run but with limited functionality.
    echo Press any key to continue anyway...
    pause >nul
)

echo Starting Enhanced Workflow V2...
echo.
echo Key Files in Use:
echo - Enhanced_Home.py: Main Streamlit interface
echo - enhanced_workflow_v2.py: Senior-level workflow engine
echo - streamlit_async_handler.py: Async task management
echo - workflow_events.py: Event-driven architecture
echo - content_enhancer.py: LLM content enhancement
echo - mind_map_generator.py: Interactive visualizations
echo - fixed_docling_processor.py: Document processing
echo.

REM Navigate to project root and launch
cd /d "%~dp0"

REM Add src to Python path and launch
set PYTHONPATH=%cd%\src;%PYTHONPATH%
streamlit run src\notebookllama\Enhanced_Home.py

echo.
echo Enhanced Workflow V2 has stopped.
pause