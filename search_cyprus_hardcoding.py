#!/usr/bin/env python3
"""
Search for Hardcoded Cyprus Data

Find where the Cyprus organization is being hardcoded in the bundle
"""

import os
import re

def search_for_cyprus_hardcoding():
    """
    Search for hardcoded Cyprus data in Python files
    """
    print("🔍 SEARCHING FOR HARDCODED CYPRUS DATA")
    print("=" * 70)
    
    # Search patterns
    patterns = [
        r"eHealthLab",
        r"University of Cyprus", 
        r"Nicosia",
        r"CY.*country",
        r"country.*CY"
    ]
    
    # Directories to search
    search_dirs = [
        "eu_ncp_server/services/",
        "patient_data/services/",
        "patient_data/",
        "eu_ncp_server/"
    ]
    
    found_files = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                for pattern in patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE)
                                    if matches:
                                        found_files.append((file_path, pattern, matches))
                                        print(f"🚨 Found '{pattern}' in {file_path}")
                                        
                                        # Show context around matches
                                        lines = content.split('\n')
                                        for i, line in enumerate(lines):
                                            if re.search(pattern, line, re.IGNORECASE):
                                                start = max(0, i-2)
                                                end = min(len(lines), i+3)
                                                print(f"   Lines {start+1}-{end}:")
                                                for j in range(start, end):
                                                    marker = ">>>" if j == i else "   "
                                                    print(f"   {marker} {j+1:3d}: {lines[j]}")
                                                print()
                        
                        except Exception as e:
                            pass  # Skip files we can't read
    
    if not found_files:
        print("✅ No hardcoded Cyprus data found in Python files")
    
    return found_files

def search_for_organization_creation():
    """
    Search for places where Organization resources are created
    """
    print("\n🔍 SEARCHING FOR ORGANIZATION RESOURCE CREATION")
    print("=" * 70)
    
    patterns = [
        r"resourceType.*Organization",
        r"Organization.*resourceType", 
        r"append.*Organization",
        r"Organization.*append"
    ]
    
    found_files = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('debug_') and not file.startswith('test_'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_files.append(file_path)
                                print(f"🎯 Found Organization creation pattern in {file_path}")
                                
                                # Show context
                                lines = content.split('\n')
                                for i, line in enumerate(lines):
                                    if re.search(pattern, line, re.IGNORECASE):
                                        start = max(0, i-3)
                                        end = min(len(lines), i+4)
                                        print(f"   Lines {start+1}-{end}:")
                                        for j in range(start, end):
                                            marker = ">>>" if j == i else "   "
                                            print(f"   {marker} {j+1:3d}: {lines[j]}")
                                        print()
                                break
                
                except Exception as e:
                    pass
    
    return found_files

if __name__ == "__main__":
    cyprus_files = search_for_cyprus_hardcoding()
    org_files = search_for_organization_creation()
    
    print(f"\n💡 SUMMARY:")
    print(f"Cyprus references found in {len(cyprus_files)} files")
    print(f"Organization creation found in {len(org_files)} files")
    
    if cyprus_files:
        print(f"\n🚨 CYPRUS DATA SOURCES:")
        for file_path, pattern, matches in cyprus_files:
            print(f"   • {file_path} ({pattern})")
    
    if org_files:
        print(f"\n📋 ORGANIZATION CREATION LOCATIONS:")
        for file_path in set(org_files):
            print(f"   • {file_path}")