#!/bin/bash

# Netcat Quick Start Script
# Installs the locked dependencies (uv.lock) with uv and starts the application.

set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "======================================"
echo "      Netcat - Network Utility"
echo "======================================"
echo ""

# uv installs the right Python version and the exact versions from uv.lock
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. See https://docs.astral.sh/uv/ (for example: brew install uv)"
    exit 1
fi

echo "uv found: $(uv --version)"
echo ""

echo "Installing dependencies from uv.lock..."
uv sync --frozen --no-dev
echo "Dependencies installed"

echo ""
echo "========================================"
echo "      Starting Netcat Application"
echo "========================================"
echo ""
echo "Access the application at: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
exec uv run --frozen --no-dev python app.py
