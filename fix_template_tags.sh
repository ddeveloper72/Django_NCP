#!/bin/bash
# Fix Django Template Tag Line Breaks
# This script fixes Django template tags that have been broken across lines by auto-formatters

echo "🔧 Fixing Django template tag line breaks..."

# Navigate to the Django project directory
cd "$(dirname "$0")"

# Fix broken template tags in all HTML files
find templates/ -name "*.html" -type f -exec sed -i '
    # Fix broken {% if statements
    s/%} *\n* *{% *if/%} {% if/g
    s/%} *\n* *{% *elif/%} {% elif/g
    s/%} *\n* *{% *else/%} {% else/g
    s/%} *\n* *{% *endif/%} {% endif/g
    
    # Fix broken {% for statements
    s/%} *\n* *{% *for/%} {% for/g
    s/%} *\n* *{% *endfor/%} {% endfor/g
    
    # Fix broken {% with statements
    s/%} *\n* *{% *with/%} {% with/g
    s/%} *\n* *{% *endwith/%} {% endwith/g
    
    # Fix broken {% comment statements
    s/%} *\n* *{% *comment/%} {% comment/g
    s/%} *\n* *{% *endcomment/%} {% endcomment/g
    
    # Fix broken {% load statements
    s/%} *\n* *{% *load/%} {% load/g
    
    # Fix broken {% block statements
    s/%} *\n* *{% *block/%} {% block/g
    s/%} *\n* *{% *endblock/%} {% endblock/g
    
    # Fix broken {% include statements
    s/%} *\n* *{% *include/%} {% include/g
    
    # Fix broken {% extends statements
    s/%} *\n* *{% *extends/%} {% extends/g
' {} \;

echo "✅ Template tag fixes applied to all HTML files in templates/ directory"

# Check for Django template syntax errors
echo "🔍 Checking for template syntax errors..."
python manage.py check --tag templates

if [ $? -eq 0 ]; then
    echo "✅ No template syntax errors found!"
else
    echo "❌ Template syntax errors detected. Please review the output above."
fi

echo "🎯 Template fix complete!"