#!/bin/bash
#
# Build script for creating macOS DMG installer
# Creates a distributable disk image with the .app bundle
#
# Requirements:
#   1. Run build_exe.py first to create dist/TelegramSignals.app
#   2. Run this script from the project root: ./scripts/build_dmg.sh
#

set -e

# Configuration
APP_NAME="TelegramSignals"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}_${VERSION}"
VOLUME_NAME="Telegram Signal Extractor"

# Paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${PROJECT_ROOT}/dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${PROJECT_ROOT}/installer/${DMG_NAME}.dmg"
STAGING_DIR="${DIST_DIR}/dmg_staging"

echo "========================================"
echo "Building macOS DMG Installer"
echo "========================================"

# Check if .app exists
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: App bundle not found: $APP_PATH"
    echo "Please run 'python scripts/build_exe.py' first"
    exit 1
fi

# Create installer directory
mkdir -p "${PROJECT_ROOT}/installer"

# Clean up any existing DMG
if [ -f "$DMG_PATH" ]; then
    echo "Removing existing DMG..."
    rm "$DMG_PATH"
fi

# Clean and create staging directory
echo "Preparing staging directory..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy app bundle to staging
echo "Copying app bundle..."
cp -R "$APP_PATH" "$STAGING_DIR/"

# Copy README
if [ -f "${DIST_DIR}/README.txt" ]; then
    cp "${DIST_DIR}/README.txt" "$STAGING_DIR/"
fi

# Create Applications symlink for drag-and-drop install
ln -s /Applications "$STAGING_DIR/Applications"

# Create DMG
echo "Creating DMG..."
hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

# Clean up staging
rm -rf "$STAGING_DIR"

echo ""
echo "========================================"
echo "DMG created successfully!"
echo "========================================"
echo "Output: $DMG_PATH"
echo ""
echo "To test: open '$DMG_PATH'"
echo ""
