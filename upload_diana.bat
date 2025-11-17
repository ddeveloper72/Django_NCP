@echo off
echo.
echo ================================================================================
echo DIANA FERREIRA - FHIR TRANSACTION BUNDLE UPLOAD TO HAPI
echo ================================================================================
echo.
echo This script will:
echo   1. Convert Diana's bundle from 'document' to 'transaction' type
echo   2. Remove placeholder IDs (like "nnn")
echo   3. Upload to HAPI FHIR server
echo   4. Verify that references were resolved
echo.
echo HAPI will automatically resolve all urn:uuid: references to actual resource IDs
echo.
pause
echo.

.venv\Scripts\python.exe upload_diana_transaction.py

echo.
pause
