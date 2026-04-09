@echo off
title Building Video Downloader...
echo ============================================
echo  Video Downloader - One-time build script
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install!
    pause
    exit /b 1
)

echo [1/3] Installing required packages...
pip install yt-dlp pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install packages.
    pause
    exit /b 1
)

echo [2/3] Building .exe (this takes ~1 minute)...
pyinstaller --onefile --windowed --name "VideoDownloader" --icon NONE app.py
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [3/3] Done!
echo.
echo Your .exe is ready at:
echo   dist\VideoDownloader.exe
echo.
echo You can now share that single file with anyone.
pause
