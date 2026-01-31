@echo off
chcp 65001 >nul
REM 自动化性能测试脚本
REM 运行程序1分钟，收集性能数据，然后导出报告

echo.
echo ============================================
echo    控制系统分析工具 - 自动化性能测试
echo ============================================
echo.
echo 测试流程:
echo   1. 启动程序（调试模式）
echo   2. 请手动切换到仿真模式并开始仿真
echo   3. 程序将自动运行 60 秒
echo   4. 自动停止并生成性能报告
echo.
echo 报告将保存为:
echo   - performance_report.txt (文本报告)
echo   - performance_data.json  (原始数据)
echo.
echo ============================================
echo.
pause

set DEBUG_MODE=1
set PERF_TEST_MODE=1
python main_perf_test.py

echo.
echo ============================================
echo    测试完成！
echo ============================================
echo.
echo 正在打开性能报告...
start notepad performance_report.txt

pause
