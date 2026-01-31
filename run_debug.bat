@echo off
REM 调试模式启动脚本
REM 启用性能监控和分析功能

echo ============================================
echo    控制系统分析工具 - 调试模式
echo ============================================
echo.
echo 启用功能:
echo   - CPU 核心利用率监控
echo   - 进程 CPU 使用率监控
echo   - 函数耗时统计
echo   - 性能瓶颈分析
echo.
echo 提示: 每 10 秒会打印一次性能报告
echo       关闭程序时会打印最终分析报告
echo ============================================
echo.

set DEBUG_MODE=1
python main.py

pause
