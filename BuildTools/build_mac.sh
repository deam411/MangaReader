#!/bin/bash
# Build script for macOS

echo "===================================="
echo "Building Manga Reader v0.0.3 for macOS"
echo "===================================="
echo

# Change to project root directory
cd "$(dirname "$0")/.."

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller"
        exit 1
    fi
fi

echo "Cleaning previous build..."
rm -rf build dist

echo
echo "Converting iconset to .icns..."
if [ -d "assets/icon.iconset" ]; then
    iconutil -c icns assets/icon.iconset -o assets/icon.icns
    if [ $? -eq 0 ]; then
        echo "Icon converted successfully"
    else
        echo "Warning: Failed to convert icon"
    fi
else
    echo "Warning: iconset not found at assets/icon.iconset"
fi

echo
echo "Building .app bundle..."
pyinstaller BuildTools/manga_reader_mac.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo
    echo "Build failed!"
    exit 1
fi

echo
echo "===================================="
echo "Build completed successfully!"
echo "Application location: dist/MangaReader.app"
echo "===================================="
echo
echo "To run: open dist/MangaReader.app"
echo "To create DMG: hdiutil create -volname MangaReader -srcfolder dist/MangaReader.app -ov -format UDZO dist/MangaReader.dmg"
