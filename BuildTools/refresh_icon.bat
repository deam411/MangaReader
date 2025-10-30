@echo off
echo ====================================
echo Refresh Icon Cache - Manga Reader
echo ====================================
echo.

echo [1/4] Eliminando vecchio exe...
cd ..
if exist "dist\MangaReader.exe" del /f "dist\MangaReader.exe"
echo     Fatto!

echo.
echo [2/4] Pulendo cache icone Windows...
cd /d %userprofile%\AppData\Local
if exist IconCache.db del /f /a IconCache.db
if exist Microsoft\Windows\Explorer attrib -h Microsoft\Windows\Explorer\iconcache*.db
if exist Microsoft\Windows\Explorer del /f Microsoft\Windows\Explorer\iconcache*.db
if exist Microsoft\Windows\Explorer del /f Microsoft\Windows\Explorer\thumbcache*.db
echo     Fatto!

echo.
echo [3/4] Riavvio Explorer per applicare...
taskkill /f /im explorer.exe >nul 2>&1
start explorer.exe
timeout /t 2 >nul
echo     Fatto!

echo.
echo [4/4] Ricompilando con icona pulita...
cd "%~dp0"
cd ..
pyinstaller BuildTools\manga_reader.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo [ERRORE] Compilazione fallita!
    pause
    exit /b 1
)

echo.
echo ====================================
echo COMPLETATO!
echo ====================================
echo.
echo Ora l'icona dovrebbe apparire correttamente!
echo Controlla: dist\MangaReader.exe
echo.
pause
