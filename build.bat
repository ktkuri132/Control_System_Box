@echo off
chcp 65001 >nul
echo ========================================
echo   控制系统分析工具 - Nuitka 编译脚本
echo ========================================
echo.

echo [1/3] 检查 Nuitka 安装...
pip show nuitka >nul 2>&1
if errorlevel 1 (
    echo Nuitka 未安装，正在安装...
    pip install nuitka ordered-set
)

echo [2/3] 开始编译...
echo 这可能需要几分钟时间，请耐心等待...
echo.

nuitka --standalone ^
    --onefile ^
    --enable-plugin=pyqt6 ^
    --windows-console-mode=disable ^
    --output-dir=dist ^
    --output-filename=ControlSystemTool.exe ^
    --company-name="ControlSystemBox" ^
    --product-name="控制系统分析工具" ^
    --file-version=2.0.0 ^
    --product-version=2.0.0 ^
    --assume-yes-for-downloads ^
    main.py

echo.
if exist "dist\ControlSystemTool.exe" (
    echo [3/3] 编译成功！
    echo 输出文件: dist\ControlSystemTool.exe
) else (
    echo [错误] 编译失败，请检查错误信息
)

echo.
pause
