#!/bin/bash
# SASS Development Watcher Script
# Automatically compiles SASS files when they change during development

echo "🚀 Starting SASS Development Watcher..."
echo "Press Ctrl+C to stop watching"

cd "$(dirname "$0")"
python compile_sass.py --watch
