#!/usr/bin/env bash
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Tesseract OCR into local directory
TESS_DIR="$PWD/tesseract_local"
mkdir -p "$TESS_DIR"

if ! command -v tesseract &> /dev/null; then
    echo "==> Downloading Tesseract packages..."
    cd /tmp

    # Download tesseract and dependencies for Ubuntu/Debian
    apt-get download tesseract-ocr tesseract-ocr-eng libtesseract5 libleptonica-dev liblept5 2>/dev/null || \
    apt-get download tesseract-ocr tesseract-ocr-eng libtesseract4 libleptonica-dev liblept5 2>/dev/null || \
    true

    # Extract .deb packages into local directory
    for deb in *.deb; do
        if [ -f "$deb" ]; then
            echo "Extracting $deb..."
            dpkg-deb -x "$deb" "$TESS_DIR"
        fi
    done

    cd -
    echo "==> Tesseract installed locally at $TESS_DIR"
    ls -la "$TESS_DIR/usr/bin/" 2>/dev/null || echo "Binary not found in expected path"
else
    echo "==> Tesseract already available: $(which tesseract)"
fi
