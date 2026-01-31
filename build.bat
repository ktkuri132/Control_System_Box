@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo  Control System Box - 构建脚本
echo ========================================
echo.

REM 设置 VS 2026 环境
echo [1] 设置 Visual Studio 2026 环境...
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 (
    echo 错误: 无法设置 VS 环境
    exit /b 1
)
echo VS 环境设置完成
echo.

REM 设置 Qt 路径
set Qt6_DIR=C:\Qt\6.10.2\msvc2022_64\lib\cmake\Qt6
set CMAKE_PREFIX_PATH=C:\Qt\6.10.2\msvc2022_64
set PATH=%PATH%;C:\Qt\6.10.2\msvc2022_64\bin

echo [2] Qt 路径: %CMAKE_PREFIX_PATH%
echo.

REM 创建 build 目录
cd /d "%~dp0"
if not exist build mkdir build
cd build

REM 运行 CMake 配置
echo [3] 运行 CMake 配置...
cmake .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="%CMAKE_PREFIX_PATH%"
if errorlevel 1 (
    echo 错误: CMake 配置失败
    exit /b 1
)
echo CMake 配置完成
echo.

REM 编译
echo [4] 开始编译...
cmake --build . --config Release -j %NUMBER_OF_PROCESSORS%
if errorlevel 1 (
    echo 错误: 编译失败
    exit /b 1
)

echo.
echo ========================================
echo  编译成功！
echo ========================================
echo 可执行文件位于: %cd%\ControlSystemBox.exe
echo.

pause
