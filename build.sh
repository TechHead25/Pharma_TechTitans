#!/bin/bash
set -e

echo "Installing dependencies with binary-only mode..."
cd pharmaguard-backend

# Update pip and ensure we have latest build tools
python -m pip install --upgrade pip setuptools wheel

# Install with --only-binary to prevent compilation
python -m pip install --only-binary :all: -r requirements-deploy.txt || \
python -m pip install -r requirements-deploy.txt

echo "Build complete!"
