# C++ Qt6 重构项目 - 快速开始指南

## 📁 项目结构

```
cpp/
├── CMakeLists.txt              # CMake 构建配置
├── include/                    # 头文件
│   ├── core/                   # 核心模块
│   │   ├── SerialManager.h     # 串口管理 ✅
│   │   ├── SimulatorReceiver.h # UDP接收 ✅
│   │   ├── DataBuffer.h        # 数据缓冲 ✅
│   │   ├── UnifiedDataProtocol.h # 协议解析 ✅
│   │   ├── SignalFilter.h      # 信号滤波 ✅
│   │   ├── PerformanceAnalyzer.h # 性能分析 ✅
│   │   └── DataProcessor.h     # 数据处理 ✅
│   └── ui/                     # UI模块
│       ├── MainWindow.h        # 主窗口 ✅
│       ├── panels/             # 控制面板
│       │   ├── UnifiedControlPanel.h ✅
│       │   ├── SerialConfigPanel.h ✅
│       │   ├── SimulatorConfigPanel.h ✅
│       │   ├── PIDControlPanel.h ✅
│       │   ├── SetpointPanel.h ✅
│       │   ├── MetricsPanel.h ✅
│       │   ├── DataControlPanel.h ✅
│       │   └── FilterPanel.h ✅
│       ├── widgets/            # 自定义控件
│       │   ├── DialWithLabel.h ✅
│       │   ├── SliderWithLabel.h ✅
│       │   ├── MetricCard.h ✅
│       │   └── StabilityGauge.h ✅
│       ├── plots/              # 图表组件
│       │   ├── RealtimePlotWidget.h ✅
│       │   ├── FFTPlotWidget.h ✅
│       │   └── SimulatorPlotWidget.h ✅
│       └── windows/            # 弹出窗口
│           ├── AnalysisWindow.h ✅
│           └── ExtendedAnalysisWindow.h ✅
├── src/                        # 源文件
│   ├── main.cpp                # 程序入口 ✅ 完整实现
│   ├── core/                   # 核心实现
│   │   ├── SerialManager.cpp   # ✅ 完整实现
│   │   ├── SimulatorReceiver.cpp # ✅ 完整实现
│   │   ├── DataBuffer.cpp      # ✅ 完整实现
│   │   ├── UnifiedDataProtocol.cpp # ✅ 完整实现
│   │   ├── SignalFilter.cpp    # ⏳ 待实现
│   │   ├── PerformanceAnalyzer.cpp # ⏳ 待实现
│   │   └── DataProcessor.cpp   # ⏳ 待实现
│   └── ui/                     # UI实现
│       ├── MainWindow.cpp      # ✅ 完整实现
│       ├── panels/*.cpp        # ⏳ 待实现
│       ├── widgets/*.cpp       # ⏳ 待实现
│       ├── plots/*.cpp         # ⏳ 待实现
│       └── windows/*.cpp       # ⏳ 待实现
├── resources/                  # 资源文件
│   ├── resources.qrc           # Qt资源配置 ✅
│   ├── images/                 # 图片资源 ✅
│   └── styles/
│       └── dark_theme.qss      # 暗色主题 ✅
└── lib/                        # 第三方库 (待添加)
    └── qcustomplot/            # 高性能图表库
```

## 🚀 构建步骤

### 1. 安装依赖

#### Windows (推荐)
1. 下载并安装 [Qt 6.6+](https://www.qt.io/download)
   - 选择组件: Qt 6.x MSVC 2022 64-bit, Qt Charts, Qt Serial Port
2. 安装 [CMake 3.16+](https://cmake.org/download/)
3. 安装 Visual Studio 2022 (或 Build Tools)

#### 可选依赖
- **QCustomPlot**: 下载 https://www.qcustomplot.com/ 放入 `lib/qcustomplot/`
- **FFTW3**: 用于高性能FFT计算
- **Eigen**: 用于矩阵运算

### 2. 构建项目

```bash
cd cpp
mkdir build && cd build

# Windows (Visual Studio)
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

# 或使用 Qt Creator 直接打开 CMakeLists.txt
```

### 3. 运行

```bash
./Release/ControlSystemBox.exe
```

## 📋 开发进度

### ✅ 已完成 (框架)
- [x] 项目目录结构
- [x] CMake 构建系统
- [x] 所有头文件定义
- [x] 核心模块实现 (SerialManager, SimulatorReceiver, DataBuffer, UnifiedDataProtocol)
- [x] 主窗口框架 (MainWindow)
- [x] 资源文件 (图标、样式表)

### ⏳ 待实现
- [ ] SignalFilter - 信号滤波算法
- [ ] PerformanceAnalyzer - 性能指标计算
- [ ] DataProcessor - 多线程数据处理
- [ ] 所有UI面板实现
- [ ] 所有自定义控件实现
- [ ] 图表组件 (使用 Qt Charts 或 QCustomPlot)
- [ ] 分析窗口实现

## 📝 开发建议

1. **优先实现顺序**:
   - 自定义控件 (DialWithLabel, SliderWithLabel)
   - 控制面板 (SerialConfigPanel, PIDControlPanel)
   - 图表组件 (RealtimePlotWidget) - 最关键
   - 分析窗口

2. **图表库选择**:
   - **Qt Charts**: 易于使用，内置于Qt
   - **QCustomPlot**: 性能更好，推荐用于实时数据

3. **测试策略**:
   - 先用模拟数据测试UI
   - 再接入真实串口/UDP测试

## 📚 参考资料

- [Qt 6 文档](https://doc.qt.io/qt-6/)
- [QCustomPlot 教程](https://www.qcustomplot.com/documentation/)
- [原Python项目 ui_config.json](../ui_config.json) - UI配置参考
- [重构方案](../REFACTORING_PLAN.md) - 详细设计文档

---

**版本**: 2.1.2  
**分支**: cpp-qt6-refactor  
**创建日期**: 2026-01-31
