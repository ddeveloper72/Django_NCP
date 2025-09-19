import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
import django
django.setup()

from django.test import Client

def examine_admin_page_content():
    client = Client()
    
    print("=== EXAMINING ADMIN PAGE CONTENT ===")
    print()
    
    # Test 1: Read the admin login page content
    print("1. Reading admin login page content...")
    response = client.get('/admin/login/')
    
    if response.status_code == 200:
        content = response.content.decode('utf-8', errors='ignore')
        
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(content)} characters")
        print(f"   Content type: {response.get('Content-Type', 'Unknown')}")
        
        # Check for key elements
        print("\n2. Checking for key HTML elements...")
        checks = [
            ('DOCTYPE', '<!DOCTYPE' in content),
            ('Title tag', '<title>' in content),
            ('Username field', 'name="username"' in content),
            ('Password field', 'name="password"' in content),
            ('Login form', '<form' in content and 'login' in content.lower()),
            ('CSS links', '<link' in content and 'css' in content),
            ('Admin branding', 'Django administration' in content),
        ]
        
        for check_name, found in checks:
            status = "✅ Found" if found else "❌ Missing"
            print(f"   {check_name}: {status}")
        
        # Look for error messages or issues
        print("\n3. Checking for potential issues...")
        issues = []
        
        if 'error' in content.lower():
            issues.append("Contains 'error' text")
        if 'exception' in content.lower():
            issues.append("Contains 'exception' text")
        if 'traceback' in content.lower():
            issues.append("Contains 'traceback' text")
        if '404' in content:
            issues.append("Contains '404' references")
        if len(content) < 1000:
            issues.append(f"Content unusually short ({len(content)} chars)")
        
        if issues:
            print("   Issues found:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print("   ✅ No obvious issues detected")
        
        # Show first part of content
        print("\n4. First 500 characters of content:")
        print("-" * 50)
        print(content[:500])
        print("-" * 50)
        
        # Show last part of content
        print("\n5. Last 500 characters of content:")
        print("-" * 50)
        print(content[-500:])
        print("-" * 50)
        
        # Look for static file references
        print("\n6. Static file references in content:")
        import re
        static_refs = re.findall(r'/static/[^"\'>\s]+', content)
        if static_refs:
            print(f"   Found {len(static_refs)} static file references:")
            for ref in static_refs[:10]:  # Show first 10
                print(f"     - {ref}")
            if len(static_refs) > 10:
                print(f"     ... and {len(static_refs) - 10} more")
        else:
            print("   ❌ No static file references found")
    
    else:
        print(f"   ❌ Failed to load admin login page: {response.status_code}")
    
    # Test 2: Check what happens when we access admin root
    print("\n7. Reading admin root redirect...")
    response = client.get('/admin/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 302:
        location = response.get('Location', 'Unknown')
        print(f"   Redirects to: {location}")
        
        # Follow the redirect
        if location:
            print("   Following redirect...")
            redirect_response = client.get(location)
            print(f"   Redirect destination status: {redirect_response.status_code}")

if __name__ == "__main__":
    examine_admin_page_content()