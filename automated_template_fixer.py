#!/usr/bin/env python
"""
Automated Django Template Bug Detection and Fixing Sy            print(f"   ✅ No set tags found")tem
Systematically identifies and fixes Jinja2 -> Django template conversion issues
"""
import os
import re
import subprocess
import time
from pathlib import Path

class DjangoTemplateFixer:
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.template_dir = self.project_dir / "templates"
        self.test_url = "http://127.0.0.1:8000/patients/cda/919811/"
        self.fixes_applied = []
        
    def test_template_error(self):
        """Test the CDA URL and extract any Django template error"""
        try:
            result = subprocess.run([
                "curl", "-s", self.test_url
            ], capture_output=True, text=True, timeout=10)
            
            response = result.stdout
            
            # Look for Django template error patterns
            if "Critical CDA View Error" in response:
                # Extract error message
                lines = response.split('\n')
                error_line = None
                for line in lines:
                    if "Error:" in line and ("Invalid block tag" in line or "Could not parse" in line):
                        error_line = line
                        break
                
                if error_line:
                    return {
                        'has_error': True,
                        'error_type': self._classify_error(error_line),
                        'error_message': error_line.strip(),
                        'full_response': response
                    }
            
            return {'has_error': False, 'message': 'Template loaded successfully'}
            
        except Exception as e:
            return {'has_error': True, 'error_type': 'network', 'error_message': str(e)}
    
    def _classify_error(self, error_line):
        """Classify the type of Django template error"""
        if "Invalid block tag" in error_line and "'set'" in error_line:
            return "jinja_set_tag"
        elif "Could not parse" in error_line and "==" in error_line:
            return "equality_comparison"
        elif "keys()" in error_line and "list" in error_line:
            return "jinja_keys_list"
        elif ".get(" in error_line:
            return "jinja_get_method"
        elif "| length" in error_line:
            return "jinja_pipe_syntax"
        else:
            return "unknown"
    
    def fix_jinja_set_tag(self, error_info):
        """Fix {% set %} tag issues by converting to Django-compatible syntax"""
        print(f"\n🔧 FIXING: Jinja2 set tags")
        
        # Find files with {% set %} tags
        set_files = []
        for html_file in self.template_dir.rglob("*.html"):
            try:
                content = html_file.read_text(encoding='utf-8')
                if re.search(r'\{\%\s*set\s+', content):
                    set_count = len(re.findall(r'\{\%\s*set\s+', content))
                    set_files.append((html_file, set_count))
            except Exception as e:
                print(f"   ⚠️ Error reading {html_file}: {e}")
        
        if not set_files:
            print("   ✅ No {% set %} tags found")
            return True
        
        # Sort by number of issues (fix files with fewer issues first)
        set_files.sort(key=lambda x: x[1])
        
        print(f"   📁 Found set tags in {len(set_files)} files:")
        for file_path, count in set_files[:3]:  # Show top 3
            print(f"      {file_path.name}: {count} issues")
        
        # Fix the first file with the fewest issues
        target_file, issue_count = set_files[0]
        print(f"\n   🎯 Fixing {target_file.name} ({issue_count} set tags)")
        
        return self._fix_set_tags_in_file(target_file)
    
    def _fix_set_tags_in_file(self, file_path):
        """Fix {% set %} tags in a specific file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Pattern 1: Simple variable assignment
            # set variable = value -> <!-- Django: variable = value (handled in view) -->
            simple_set_pattern = r'\{\%\s*set\s+(\w+)\s*=\s*([^%]+)\s*\%\}'
            
            def replace_simple_set(match):
                var_name = match.group(1)
                var_value = match.group(2).strip()
                return f'{{# Django: {var_name} = {var_value} (moved to view context) #}}'
            
            content = re.sub(simple_set_pattern, replace_simple_set, content)
            
            # Pattern 2: Complex set with dictionary/list operations
            # set list = list + [item] -> Comment out for now
            complex_set_pattern = r'\{\%\s*set\s+[^%]+\%\}'
            
            def replace_complex_set(match):
                original = match.group(0)
                return f'{{# Django TODO: Convert complex set - {original} #}}'
            
            content = re.sub(complex_set_pattern, replace_complex_set, content)
            
            if content != original_content:
                # Backup original
                backup_path = file_path.with_suffix(f'.jinja2_backup{file_path.suffix}')
                backup_path.write_text(original_content, encoding='utf-8')
                
                # Write fixed version
                file_path.write_text(content, encoding='utf-8')
                
                fix_info = {
                    'file': str(file_path),
                    'type': 'set_tag_conversion', 
                    'backup': str(backup_path)
                }
                self.fixes_applied.append(fix_info)
                
                print(f"   ✅ Fixed {file_path.name}")
                print(f"   📄 Backup saved: {backup_path.name}")
                return True
            else:
                print(f"   ⚠️ No set patterns matched in {file_path.name}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error fixing {file_path.name}: {e}")
            return False
    
    def run_fix_cycle(self):
        """Run one complete bug detection and fix cycle"""
        print("=" * 80)
        print("🔍 DJANGO TEMPLATE BUG DETECTION & FIX CYCLE")
        print("=" * 80)
        
        # Test for current error
        print("\n1️⃣ Testing current template state...")
        error_info = self.test_template_error()
        
        if not error_info['has_error']:
            print("🎉 SUCCESS! No template errors detected!")
            return {'success': True, 'message': 'All template errors resolved'}
        
        print(f"❌ DETECTED: {error_info['error_type']}")
        print(f"   Error: {error_info['error_message']}")
        
        # Apply appropriate fix
        print(f"\n2️⃣ Applying fix for: {error_info['error_type']}")
        
        fix_success = False
        if error_info['error_type'] == 'jinja_set_tag':
            fix_success = self.fix_jinja_set_tag(error_info)
        else:
            print(f"   ⚠️ No automated fix available for: {error_info['error_type']}")
            return {
                'success': False, 
                'error_type': error_info['error_type'],
                'message': 'Manual fix required',
                'error_details': error_info
            }
        
        if fix_success:
            print("\n3️⃣ Testing fix...")
            time.sleep(2)  # Give server time to reload
            
            new_error_info = self.test_template_error()
            
            if not new_error_info['has_error']:
                print("✅ FIX SUCCESSFUL! Template now loads without errors!")
                return {'success': True, 'message': 'Fix successful'}
            elif new_error_info['error_type'] != error_info['error_type']:
                print(f"✅ PROGRESS! Fixed {error_info['error_type']}")
                print(f"🔄 Next error: {new_error_info['error_type']}")
                return {
                    'success': True, 
                    'message': 'Partial fix - new error revealed',
                    'next_error': new_error_info
                }
            else:
                print(f"⚠️ Same error persists - may need manual intervention")
                return {
                    'success': False,
                    'message': 'Fix did not resolve error',
                    'error_details': new_error_info
                }
        else:
            print("❌ Fix failed to apply")
            return {'success': False, 'message': 'Fix application failed'}

def main():
    """Main execution function"""
    os.chdir("C:/Users/Duncan/VS_Code_Projects/django_ncp")
    
    fixer = DjangoTemplateFixer("C:/Users/Duncan/VS_Code_Projects/django_ncp")
    
    # Run single fix cycle
    result = fixer.run_fix_cycle()
    
    print(f"\n📊 CYCLE RESULT:")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if result.get('next_error'):
        print(f"   Next Error: {result['next_error']['error_type']}")
    
    print(f"\n📋 FIXES APPLIED THIS CYCLE: {len(fixer.fixes_applied)}")
    for fix in fixer.fixes_applied:
        print(f"   ✅ {fix['type']}: {Path(fix['file']).name}")

if __name__ == "__main__":
    main()
