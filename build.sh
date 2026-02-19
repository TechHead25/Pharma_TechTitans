#!/bin/bash
set -e

echo "Python version:"
python --version

echo "Installing dependencies..."
cd pharmaguard-backend

# Update pip and build tools
python -m pip install --upgrade pip setuptools wheel

# Install packages
python -m pip install -r requirements-deploy.txt

echo "Build complete!"
