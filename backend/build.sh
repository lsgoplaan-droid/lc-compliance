#!/usr/bin/env bash
set -o errexit

# Install Tesseract OCR
apt-get update && apt-get install -y --no-install-recommends tesseract-ocr

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
