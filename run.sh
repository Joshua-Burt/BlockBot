#!/bin/bash

SCRIPT_DIR=$(dirname "$0")

cd "${SCRIPT_DIR}"/src || exit

# This assumes it is pointing to python >= v3.10
python -u main.py