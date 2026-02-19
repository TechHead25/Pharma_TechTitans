#!/bin/bash
set -e

echo "Python version:"
python --version

echo "Installing dependencies with pip..."

# Update pip and build tools
python -m pip install --upgrade pip setuptools wheel

# Install packages - pydantic-core 2.27.0+ supports Python 3.14
python -m pip install -r requirements-deploy.txt

echo "Build complete!"
