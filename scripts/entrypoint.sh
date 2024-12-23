#!/bin/bash
set -e

# Initialize ansible environment if needed
if [ ! -f "~/.ssh/known_hosts" ]; then
    mkdir -p ~/.ssh
    touch ~/.ssh/known_hosts
fi

# Start Streamlit
exec streamlit run /app/src/main.py
