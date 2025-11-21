#!/bin/bash
# Configure ODBC for FreeTDS on Heroku

# Set ODBC configuration path
export ODBCSYSINI=/app
export ODBCINI=/app/.odbc.ini
export ODBCINSTINI=/app/.odbcinst.ini

# Copy our ODBC configuration
cp /app/.odbcinst.ini /etc/odbcinst.ini 2>/dev/null || true

# Display available drivers for debugging
echo "Available ODBC drivers:"
python -c "import pyodbc; print(pyodbc.drivers())" 2>/dev/null || echo "Could not list drivers"
