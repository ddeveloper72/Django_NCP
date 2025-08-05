#!/usr/bin/env python
"""
Final targeted replacement for specific remaining hardcoded strings
"""

def apply_targeted_replacements():
    template_file = 'templates/jinja2/patient_data/patient_cda.html'
    
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Specific targeted replacements for remaining violations
    specific_replacements = [
        # English Translation headers
        ('>\n                                                English Translation\n                                            <',
         '>{{ template_translations.english_translation if template_translations else "English Translation" }}<'),
         
        ('>\n                                            English Translation\n                                        <',
         '>{{ template_translations.english_translation if template_translations else "English Translation" }}<'),
         
        # Technical Error
        ('>Technical Error<',
         '>{{ template_translations.technical_error if template_translations else "Technical Error" }}<'),
    ]
    
    modified = False
    replacement_count = 0
    
    for pattern, replacement in specific_replacements:
        if pattern in content:
            content = content.replace(pattern, replacement)
            modified = True
            replacement_count += 1
            print(f"✅ Replaced: {pattern[:40]}...")
    
    if modified:
        # Write updated content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n🎯 TARGETED REPLACEMENT COMPLETE")
        print(f"🔄 Replacements made: {replacement_count}")
    else:
        print("ℹ️  No targeted patterns found")
    
    return modified, replacement_count

if __name__ == "__main__":
    print("=== TARGETED TEMPLATE REPLACEMENT ===")
    apply_targeted_replacements()
    print("=== COMPLETE ===")
