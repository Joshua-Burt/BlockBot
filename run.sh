#!/bin/bash

SCRIPT_DIR=$(dirname "$0")

cd "${SCRIPT_DIR}"/src || exit

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Validate version using Python's internal version_info system
# Python 3.10 is the minimum version of Python required for py-cord.
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "Error: Python version must be 3.10 or above."
    echo "Current version: $(python3 --version)"
    exit 1
fi

# This assumes it is pointing to python >= v3.10
python3 -u main.py