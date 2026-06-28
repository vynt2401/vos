@echo off
echo ==========================================
echo   IoT Gateway C++ Qt5 - MSYS2 Build
echo ==========================================
echo.
echo Mo MSYS2 UCRT64 roi chay script nay.
echo.

where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] cmake khong tim thay.
    echo Cai trong MSYS2 UCRT64:
    echo   pacman -S mingw-w64-ucrt-x86_64-cmake
    pause
    exit /b 1
)

where qmake >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Qt5 khong tim thay.
    echo Cai trong MSYS2 UCRT64:
    echo   pacman -S mingw-w64-ucrt-x86_64-qt5-base
    pause
    exit /b 1
)

echo [1/3] Tao build directory...
if not exist build mkdir build
cd build

echo [2/3] Configuring...
cmake .. -G "MinGW Makefiles" -DCMAKE_PREFIX_PATH=C:/msys64/ucrt64
if %errorlevel% neq 0 (
    echo [ERROR] cmake that bai.
    pause
    exit /b 1
)

echo [3/3] Building...
cmake --build . --config Release -j4
if %errorlevel% neq 0 (
    echo [ERROR] build that bai.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Build thanh cong!
echo   Chay: build\iot-gateway.exe
echo ==========================================
pause
