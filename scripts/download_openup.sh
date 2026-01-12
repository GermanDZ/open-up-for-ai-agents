#!/bin/bash

# Download and extract OpenUP source files
# Eclipse EPF OpenUP 1.5.1.5 (December 12, 2012)

set -e  # Exit on error

DOWNLOAD_URL="https://archive.eclipse.org/epf/downloads/OpenUP/published/openup_published_1.5.1.5_20121212.zip"
OUTPUT_DIR=".tmp"
ZIP_FILE="$OUTPUT_DIR/openup.zip"
EXTRACT_DIR="$OUTPUT_DIR/openup"

echo "================================================"
echo "OpenUP Source Files Downloader"
echo "================================================"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Download if not already present
if [ -f "$ZIP_FILE" ]; then
    echo "✓ ZIP file already exists: $ZIP_FILE"
else
    echo "Downloading OpenUP source files (~15 MB)..."
    echo "URL: $DOWNLOAD_URL"

    if command -v curl &> /dev/null; then
        curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$ZIP_FILE" "$DOWNLOAD_URL"
    else
        echo "Error: Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    echo "✓ Download complete"
fi

# Extract if not already extracted
if [ -d "$EXTRACT_DIR" ]; then
    echo "✓ Files already extracted: $EXTRACT_DIR"
else
    echo "Extracting archive..."
    unzip -q "$ZIP_FILE" -d "$OUTPUT_DIR"

    # Rename extracted directory to 'openup'
    EXTRACTED_NAME=$(unzip -l "$ZIP_FILE" | grep -m1 "/$" | awk '{print $4}' | cut -d'/' -f1)
    if [ -n "$EXTRACTED_NAME" ] && [ "$EXTRACTED_NAME" != "openup" ]; then
        mv "$OUTPUT_DIR/$EXTRACTED_NAME" "$EXTRACT_DIR"
    fi

    echo "✓ Extraction complete"
fi

# Verify HTML files
HTML_COUNT=$(find "$EXTRACT_DIR" -name "*.html" -type f 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "================================================"
echo "✓ Setup complete!"
echo "================================================"
echo "Location: $EXTRACT_DIR"
echo "HTML files: $HTML_COUNT"
echo ""
echo "You can now run the converter:"
echo "  python3 scripts/convert.py"
echo ""
