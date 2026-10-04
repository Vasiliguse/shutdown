@echo off
setlocal

py -m pip install -r requirements.txt
py -m PyInstaller --onefile --windowed --name ShutdownTimer --clean shutdown_timer_final.py

if exist dist\ShutdownTimer.exe (
    echo.
    echo Build complete: dist\ShutdownTimer.exe
) else (
    echo.
    echo Build failed. Check the command output above.
    exit /b 1
)
