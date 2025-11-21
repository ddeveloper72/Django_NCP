#!/bin/bash
# Configure ODBC for FreeTDS on Heroku

# Set library path for apt packages
export LD_LIBRARY_PATH=/app/.apt/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Find FreeTDS library
FREETDS_LIB=$(find /app/.apt/usr/lib -name "libtdsodbc.so" 2>/dev/null | head -n1)

if [ ! -z "$FREETDS_LIB" ]; then
    # Create ODBC configuration with correct path
    cat > /app/.odbcinst.ini <<EOF
[FreeTDS]
Description = FreeTDS Driver for SQL Server
Driver = $FREETDS_LIB
UsageCount = 1
EOF
    
    # Set ODBC configuration path
    export ODBCSYSINI=/app
    export ODBCINI=/app/.odbc.ini
    export ODBCINSTINI=/app/.odbcinst.ini
    
    echo "🔧 FreeTDS configured at: $FREETDS_LIB"
else
    echo "⚠️  FreeTDS library not found"
fi

# Display available drivers for debugging
echo "Available ODBC drivers:"
python -c "import pyodbc; print(pyodbc.drivers())" 2>/dev/null || echo "Could not list drivers"
