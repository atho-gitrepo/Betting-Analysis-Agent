#!/bin/bash

# Get PORT from Railway (default to 8080)
PORT=${PORT:-8080}
echo "Starting services on port: $PORT"

# Create streamlit config with correct port
mkdir -p .streamlit
cat > .streamlit/config.toml << CONFIG
[server]
address = "0.0.0.0"
port = $PORT
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[logger]
level = "info"
CONFIG

# Start the process manager
exec python process_manager.py