@echo off
echo Building WWM Auto-Bard...
echo.

REM Activate virtual environment
call .venv\Scripts\activate

REM Install PyInstaller if not present
pip show pyinstaller >nul 2>&1 || pip install pyinstaller

REM Build the executable
pyinstaller wwm_autobard.spec --clean

echo.
echo Build complete! Executable is in dist\WWM_AutoBard.exe
pause
