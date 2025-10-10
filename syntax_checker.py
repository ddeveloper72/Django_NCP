#!/usr/bin/env python3
"""
Simple syntax checker for patient_data/views.py
Attempts to identify the exact line and issue causing syntax problems.
"""

import ast
import sys


def check_syntax_with_line_info():
    """Check syntax and provide detailed error information."""
    try:
        # Read file with explicit UTF-8 encoding
        with open('patient_data/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"File length: {len(content)} characters")
        lines = content.split('\n')
        print(f"Total lines: {len(lines)}")
        
        # Try to parse the content
        ast.parse(content)
        print("✅ File syntax is valid")
        
    except SyntaxError as e:
        print(f"❌ Syntax error at line {e.lineno}, column {e.offset}")
        print(f"Error message: {e.msg}")
        
        if e.text:
            print(f"Problematic line: {e.text.strip()}")
        
        # Show context around the error
        if e.lineno:
            start_line = max(1, e.lineno - 3)
            end_line = min(len(lines), e.lineno + 3)
            
            print("\nContext:")
            for i in range(start_line - 1, end_line):
                marker = ">>> " if i + 1 == e.lineno else "    "
                print(f"{marker}{i + 1:4d}: {lines[i]}")
                
    except UnicodeDecodeError as e:
        print(f"❌ Unicode decode error: {e}")
        print("File contains non-UTF-8 characters")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    check_syntax_with_line_info()