#!/usr/bin/env python3
"""
Diagnose template block structure issues
"""

import re
import os


def diagnose_block_structure(file_path):
    """Diagnose block structure around the problem area"""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("Block structure analysis around line 446:")
    print("=" * 60)

    # Analyze from line 420 to 480
    start_line = 420
    end_line = 480
    block_stack = []

    for line_num in range(start_line, min(end_line, len(lines))):
        line = lines[line_num]
        actual_line_num = line_num + 1

        # Find block tags
        if_matches = re.findall(r"\{% if [^%]*%\}", line)
        elif_matches = re.findall(r"\{% elif [^%]*%\}", line)
        else_matches = re.findall(r"\{% else [^%]*%\}", line)
        endif_matches = re.findall(r"\{% endif [^%]*%\}", line)
        for_matches = re.findall(r"\{% for [^%]*%\}", line)
        endfor_matches = re.findall(r"\{% endfor [^%]*%\}", line)

        # Track opening tags
        for match in if_matches:
            block_stack.append(("if", actual_line_num))
            print(
                f"Line {actual_line_num}: OPEN 'if' - Stack depth: {len(block_stack)}"
            )

        for match in for_matches:
            block_stack.append(("for", actual_line_num))
            print(
                f"Line {actual_line_num}: OPEN 'for' - Stack depth: {len(block_stack)}"
            )

        # Track elif/else
        for match in elif_matches:
            print(
                f"Line {actual_line_num}: 'elif' - Current stack: {[t[0] for t in block_stack]}"
            )

        for match in else_matches:
            print(
                f"Line {actual_line_num}: 'else' - Current stack: {[t[0] for t in block_stack]}"
            )

        # Track closing tags
        for match in endif_matches:
            if block_stack:
                last_type, last_line = block_stack[-1]
                if last_type == "if":
                    block_stack.pop()
                    print(
                        f"Line {actual_line_num}: CLOSE 'endif' (matches 'if' from line {last_line}) - Stack depth: {len(block_stack)}"
                    )
                else:
                    print(
                        f"Line {actual_line_num}: ❌ ERROR 'endif' but expected 'end{last_type}' from line {last_line}"
                    )
            else:
                print(
                    f"Line {actual_line_num}: ❌ ERROR 'endif' with no matching opening tag"
                )

        for match in endfor_matches:
            if block_stack:
                last_type, last_line = block_stack[-1]
                if last_type == "for":
                    block_stack.pop()
                    print(
                        f"Line {actual_line_num}: CLOSE 'endfor' (matches 'for' from line {last_line}) - Stack depth: {len(block_stack)}"
                    )
                else:
                    print(
                        f"Line {actual_line_num}: ❌ ERROR 'endfor' but expected 'end{last_type}' from line {last_line}"
                    )
            else:
                print(
                    f"Line {actual_line_num}: ❌ ERROR 'endfor' with no matching opening tag"
                )

    print("\nRemaining unclosed blocks:")
    for block_type, line_num in block_stack:
        print(f"  Line {line_num}: Unclosed '{block_type}' block")


def main():
    template_file = r"C:\Users\Duncan\VS_Code_Projects\django_ncp\templates\jinja2\patient_data\enhanced_patient_cda.html"

    if os.path.exists(template_file):
        diagnose_block_structure(template_file)
    else:
        print(f"❌ Template file not found: {template_file}")


if __name__ == "__main__":
    main()
