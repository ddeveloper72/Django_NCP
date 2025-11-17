@echo off
echo.
echo ================================================================================
echo CHECK HAPI REFERENCES - Diana Ferreira
echo ================================================================================
echo.
echo This will check if Diana's Composition on HAPI has properly resolved references
echo.

.venv\Scripts\python.exe check_hapi_references.py

echo.
pause
