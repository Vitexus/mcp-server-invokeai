#!/bin/bash
# Setup script for InvokeAI MCP Server

set -e

echo "=== InvokeAI MCP Server Setup ==="
echo

# Check if python3-venv is available
if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed."
    echo "Please install it with: sudo apt install python3-venv"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "=== Setup Complete! ==="
echo
echo "To configure Claude Code, add this to ~/.config/claude-code/mcp_config.json:"
echo
cat mcp_config.example.json
echo
echo "Then restart Claude Code to use the InvokeAI server."
