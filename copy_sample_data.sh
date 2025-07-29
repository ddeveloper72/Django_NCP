#!/bin/bash
# Script to copy sample patient data from OpenNCP integration folder
# Run this from the django_ncp project root directory

SOURCE_DIR="C:/Users/Duncan/VS_Code_Projects/ehealth-2/openncp-docker/openncp-configuration/integration"
TARGET_DIR="C:/Users/Duncan/VS_Code_Projects/django_ncp/patient_data/sample_data/integration"

echo "Copying sample patient data from OpenNCP integration folder..."

if [ -d "$SOURCE_DIR" ]; then
    # Copy all OID subdirectories and their contents
    cp -r "$SOURCE_DIR"/* "$TARGET_DIR"/
    echo "Sample data copied successfully!"
    echo "Contents of integration folder:"
    ls -la "$TARGET_DIR"
else
    echo "Source directory not found: $SOURCE_DIR"
    echo "Please check the path and try again."
fi
