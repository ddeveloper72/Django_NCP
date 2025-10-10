#!/usr/bin/env python3

def restore_original_indentation():
    """Restore the original indentation to match the working commit"""
    
    with open('patient_data/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # The try block is now at line 4901 with 8 spaces
    # Content from line 4902 to line 5872 needs to be at 12+ spaces (inside the try block)
    
    changes = 0
    for i in range(4901, 5872):  # 0-indexed range
        if i < len(lines):
            line = lines[i]
            # Only modify lines that have less than 12 spaces of indentation
            if line.strip() and line.startswith('        ') and not line.startswith('            '):  # exactly 8 spaces
                # Add 4 more spaces to make it 12 spaces (inside the try block)
                lines[i] = '    ' + line
                changes += 1
    
    print(f"Updated {changes} lines to restore original indentation")
    
    with open('patient_data/views.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    restore_original_indentation()