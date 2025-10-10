#!/usr/bin/env python3

def find_unmatched_try_blocks():
    """Find unmatched try blocks by tracking indentation levels"""
    
    with open('patient_data/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    try_stack = []  # Stack to track try blocks with their line numbers and indentation
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('try:'):
            # Count leading spaces
            indent = len(line) - len(line.lstrip())
            try_stack.append((i + 1, indent))  # 1-based line number
            print(f"Found try at line {i + 1}, indent {indent}")
        
        elif stripped.startswith('except ') or stripped == 'except:':
            if try_stack:
                # Count leading spaces
                indent = len(line) - len(line.lstrip())
                # Find matching try block (same or less indentation)
                matched = False
                for j in range(len(try_stack) - 1, -1, -1):
                    try_line, try_indent = try_stack[j]
                    if try_indent == indent:
                        print(f"Matched except at line {i + 1} (indent {indent}) with try at line {try_line}")
                        try_stack.pop(j)
                        matched = True
                        break
                
                if not matched:
                    print(f"WARNING: except at line {i + 1} (indent {indent}) has no matching try")
        
        elif stripped.startswith('finally:'):
            if try_stack:
                # Count leading spaces
                indent = len(line) - len(line.lstrip())
                # Find matching try block (same indentation)
                for j in range(len(try_stack) - 1, -1, -1):
                    try_line, try_indent = try_stack[j]
                    if try_indent == indent:
                        print(f"Matched finally at line {i + 1} (indent {indent}) with try at line {try_line}")
                        try_stack.pop(j)
                        break
    
    print("\nUnmatched try blocks:")
    for try_line, try_indent in try_stack:
        print(f"Line {try_line}: {try_indent} spaces - UNMATCHED TRY")

if __name__ == "__main__":
    find_unmatched_try_blocks()