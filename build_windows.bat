@echo off
echo ========================================================
echo        Building Timer for Windows (Timer.exe)
echo ========================================================

REM Ensure python and pyinstaller are installed
python -m pip install --upgrade pip
pip install pyinstaller pillow pystray

REM Build single-file Windows executable
pyinstaller --onefile --noconsole --name "Timer" --icon "assets\timer.ico" --add-data "assets;assets" run.py

if exist "dist\Timer.exe" (
    echo.
    echo ========================================================
    echo Build Successful: dist\Timer.exe
    echo ========================================================
    powershell -Command "Compress-Archive -Path dist\Timer.exe, assets -DestinationPath Timer-windows-x64.zip -Force"
    echo Created archive: Timer-windows-x64.zip
) else (
    echo [ERROR] Build failed. Check output above.
)
pause
