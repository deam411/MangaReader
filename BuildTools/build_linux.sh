#!/bin/bash
# Build script for Linux

echo "===================================="
echo "Building Manga Reader v0.0.3 for Linux"
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
echo "Building Linux executable..."
pyinstaller BuildTools/manga_reader_linux.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo
    echo "Build failed!"
    exit 1
fi

# Make executable
chmod +x dist/MangaReader

echo
echo "===================================="
echo "Build completed successfully!"
echo "Executable location: dist/MangaReader"
echo "===================================="
echo
echo "To run: ./dist/MangaReader"
