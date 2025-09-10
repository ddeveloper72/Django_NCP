@echo off
REM SASS Development Watcher Script for Windows
REM Automatically compiles SASS files when they change during development

echo 🚀 Starting SASS Development Watcher...
echo Press Ctrl+C to stop watching

cd /d "%~dp0"
python compile_sass.py --watch
