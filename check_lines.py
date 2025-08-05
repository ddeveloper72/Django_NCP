with open("templates/jinja2/patient_data/patient_cda.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Check specific line numbers mentioned in test
check_lines = [296, 426, 449, 498, 607, 618]

for line_num in check_lines:
    if line_num <= len(lines):
        line = lines[line_num - 1].strip()
        print(f"Line {line_num}: {line}")
    else:
        print(f"Line {line_num}: NOT FOUND")
