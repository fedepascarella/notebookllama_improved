@echo off
echo ========================================
echo   Stopping NotebookLlama Enhanced
echo ========================================
echo.

echo Stopping Docker services...
docker-compose stop

echo.
echo Services stopped.
echo.
echo To completely remove containers and networks (keeps data):
echo   docker-compose down
echo.
echo To remove everything including data volumes (WARNING: deletes all data):
echo   docker-compose down -v
echo.
pause