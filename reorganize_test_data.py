#!/usr/bin/env python3
"""
Test Data Reorganization Script
Reorganizes EU member state CDA documents for better search performance
"""

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_patient_info_from_cda(file_path: Path) -> dict:
    """Extract patient information from CDA document"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Define namespace
        ns = {'cda': 'urn:hl7-org:v3'}
        
        # Extract patient info
        patient_info = {}
        
        # Find patient role
        patient_role = root.find('.//cda:recordTarget/cda:patientRole', ns)
        if patient_role is not None:
            # Patient ID
            patient_id_elem = patient_role.find('.//cda:id', ns)
            if patient_id_elem is not None:
                patient_info['patient_id'] = patient_id_elem.get('extension', '')
                patient_info['patient_id_root'] = patient_id_elem.get('root', '')
            
            # Patient name
            patient_elem = patient_role.find('.//cda:patient', ns)
            if patient_elem is not None:
                name_elem = patient_elem.find('.//cda:name', ns)
                if name_elem is not None:
                    family_elem = name_elem.find('.//cda:family', ns)
                    given_elem = name_elem.find('.//cda:given', ns)
                    
                    if family_elem is not None:
                        patient_info['family_name'] = family_elem.text or ''
                    if given_elem is not None:
                        patient_info['given_name'] = given_elem.text or ''
        
        # Extract country from realmCode
        realm_code = root.find('.//cda:realmCode', ns)
        if realm_code is not None:
            patient_info['country_code'] = realm_code.get('code', '')
        
        return patient_info
        
    except Exception as e:
        logger.warning(f"Error parsing {file_path}: {e}")
        return {}


def reorganize_test_data():
    """Reorganize test data into a cleaner structure"""
    
    base_path = Path("test_data/eu_member_states")
    backup_path = Path("test_data/eu_member_states_backup")
    
    # Create backup if it doesn't exist
    if not backup_path.exists() and base_path.exists():
        logger.info("Creating backup of original test data...")
        shutil.copytree(base_path, backup_path)
        logger.info(f"Backup created at {backup_path}")
    
    # Find all XML files
    xml_files = []
    if base_path.exists():
        xml_files = list(base_path.rglob("*.xml"))
    
    logger.info(f"Found {len(xml_files)} XML files to process")
    
    # Process each file
    organized_files = {}
    
    for xml_file in xml_files:
        logger.info(f"Processing: {xml_file}")
        
        # Extract patient info
        patient_info = extract_patient_info_from_cda(xml_file)
        
        if not patient_info:
            logger.warning(f"Could not extract patient info from {xml_file}")
            continue
        
        country_code = patient_info.get('country_code', 'UNKNOWN')
        patient_id = patient_info.get('patient_id', 'unknown_patient')
        family_name = patient_info.get('family_name', 'Unknown')
        given_name = patient_info.get('given_name', 'Unknown')
        
        # Create a clean filename
        clean_name = f"{given_name}_{family_name}".replace(' ', '_')
        if patient_id and patient_id != 'unknown_patient':
            clean_name += f"_{patient_id[:8]}"  # First 8 chars of patient ID
        
        # Remove special characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in ['_', '-'])
        new_filename = f"{clean_name}.xml"
        
        # Create country directory
        country_dir = base_path / country_code.upper()
        country_dir.mkdir(parents=True, exist_ok=True)
        
        # New file path
        new_file_path = country_dir / new_filename
        
        # Handle duplicates
        counter = 1
        original_new_file_path = new_file_path
        while new_file_path.exists():
            stem = original_new_file_path.stem
            suffix = original_new_file_path.suffix
            new_file_path = country_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Copy file to new location (if it's not already there)
        if xml_file != new_file_path:
            try:
                shutil.copy2(xml_file, new_file_path)
                logger.info(f"  → Copied to: {new_file_path}")
                
                # Store info about organized files
                if country_code not in organized_files:
                    organized_files[country_code] = []
                organized_files[country_code].append({
                    'original_path': str(xml_file),
                    'new_path': str(new_file_path),
                    'patient_info': patient_info
                })
                
            except Exception as e:
                logger.error(f"Error copying {xml_file} to {new_file_path}: {e}")
    
    # Clean up old nested directories
    logger.info("Cleaning up old directory structure...")
    for country_dir in base_path.iterdir():
        if country_dir.is_dir():
            # Remove empty subdirectories
            for root, dirs, files in os.walk(country_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if not any(dir_path.iterdir()):  # Directory is empty
                            dir_path.rmdir()
                            logger.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other issue
    
    # Generate summary report
    logger.info("\n=== REORGANIZATION SUMMARY ===")
    total_files = 0
    for country, files in organized_files.items():
        logger.info(f"{country}: {len(files)} files")
        total_files += len(files)
        for file_info in files:
            patient_info = file_info['patient_info']
            logger.info(f"  - {patient_info.get('given_name', 'Unknown')} {patient_info.get('family_name', 'Unknown')} (ID: {patient_info.get('patient_id', 'N/A')})")
    
    logger.info(f"\nTotal files organized: {total_files}")
    logger.info(f"Backup available at: {backup_path}")
    
    return organized_files


if __name__ == "__main__":
    reorganize_test_data()
