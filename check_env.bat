@echo off
chcp 65001 >nul
echo ========================================
echo   Control System Box - 环境检测
echo ========================================
echo.

echo [1] 检查 CMake...
where cmake 2>nul
if %errorlevel%==0 (
    cmake --version
) else (
    echo CMake 未找到，请确保已安装并添加到PATH
)
echo.

echo [2] 检查 Visual Studio...
set VSWHERE="%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if exist %VSWHERE% (
    %VSWHERE% -latest -property displayName
    %VSWHERE% -latest -property installationPath
) else (
    echo vswhere 未找到
)
echo.

echo [3] 检查 Qt...
where qmake 2>nul
if %errorlevel%==0 (
    qmake --version
) else (
    echo Qt 未在 PATH 中找到
    echo 检查常见 Qt 安装路径...
    if exist "C:\Qt" (
        echo 发现 C:\Qt 目录
        dir /b "C:\Qt" 2>nul
    )
)
echo.

echo [4] 检查 MSBuild...
where msbuild 2>nul
if %errorlevel%==0 (
    msbuild -version
) else (
    echo MSBuild 未在 PATH 中
)
echo.

echo ========================================
echo 检测完成
echo ========================================
pause
