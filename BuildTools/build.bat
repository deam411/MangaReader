@echo off
echo ====================================
echo Building Manga Reader v0.1.5.1
echo ====================================
echo.

REM Change to project root directory
cd ..

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Building executable...
pyinstaller BuildTools\manga_reader.spec

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ====================================
echo Build completed successfully!
echo.
echo Executable: dist\MangaReader.exe
echo ====================================
echo.
pause
