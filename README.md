# Control System Box

控制系统实时分析工具（C++/Qt6）。

当前版本: `v2.3.0`

## 功能概览

- 串口与 UDP 双数据源接入
- 多状态变量实时曲线显示
- 混合渲染绘图（Qt + Vulkan）
- 滤波、指标分析、频谱分析面板
- 主进程渲染 + 计算进程架构（worker 子进程）

## 项目结构

```text
Control_System_Box/
├── CMakeLists.txt
├── include/
│   ├── core/
│   └── ui/
├── src/
│   ├── core/
│   └── ui/
├── resources/
└── cmake-build-debug/
```

## 构建与运行（Windows）

依赖环境:

- Qt 6.10.2 (MSVC 2022 x64)
- CMake >= 3.16
- Visual Studio 2022 Build Tools
- Vulkan SDK

构建:

```powershell
cmake -S . -B cmake-build-debug
cmake --build cmake-build-debug --config Debug
```

运行:

```powershell
./cmake-build-debug/ControlSystemBox.exe
```

## 数据协议

支持以下输入形式:

- 串口文本协议（`#H` / `#D`）
- UDP JSON 协议（`HANDSHAKE` / `DATA`）
- UDP 兼容旧格式（嵌套 `state`/`target`/`control`）

默认 UDP 监听地址为 `0.0.0.0:5555`。

## 版本变更

### v2.3.0

- 统一并整理版本号
- 优化 UDP 接收与旧协议兼容性
- 改进图表批量更新，减少启动阶段曲线异常
- 更新 README，移除过时的“待实现”说明

### v2.2.0

- 双进程架构：主进程渲染 + 计算进程
- 统一调试日志控制与输出节流

## 说明

- `cmake-build-debug/` 为本地构建输出目录，不建议提交到版本库。
- 若遇到链接错误 `LNK1168`，请先关闭正在运行的 `ControlSystemBox.exe`。
