@echo off
echo ==========================================
echo   IoT Gateway - Install Dependencies
echo ==========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python chua cai. Tai tu https://python.org
    pause
    exit /b 1
)

echo [1/2] Cai dat dependencies...
pip install -r requirements.txt

echo.
echo [2/2] Kiem tra...
python -c "import PyQt5; print('PyQt5:', PyQt5.QtCore.PYQT_VERSION_STR)"
python -c "import paho.mqtt; print('paho-mqtt OK')"
python -c "import pymodbus; print('pymodbus OK')"

echo.
echo ==========================================
echo   Install xong! Chay: run.bat
echo ==========================================
pause
