# 控制系统实时分析工具 v2.1.1

统一架构版本 - 串口和仿真共用相同的核心组件。

## 功能特性

- 📈 **实时数据可视化**：高性能实时绑图，支持多状态变量选择
- 🔌 **双数据源支持**：串口 + UDP仿真，统一处理流程
- 🎛️ **PID参数调节**：旋钮和滑块交互，支持实时发送
- 📊 **性能指标计算**：上升时间、调节时间、超调量、稳态误差等
- 💾 **数据导出**：支持导出为CSV文件
- 🎯 **状态选择器**：动态选择要观察的状态变量
- 🔬 **信号滤波**：多种滤波算法，可调节强度
- ⚡ **多进程加速**：充分利用多核CPU提升性能

## v2.1.1 更新内容

- 🚀 **性能大幅优化**：使用多进程处理数据，减少卡顿
- 📊 **调试性能分析器**：支持 CPU 核心使用率监控
- 🎨 **渲染优化**：OpenGL 加速、降采样、禁用抗锯齿
- 🔧 **滤波器改进**：滤波计算移至独立进程

## 系统要求

- Python 3.10+
- Windows / Linux / macOS

## 安装依赖

```bash
pip install PyQt6 pyqtgraph pyserial numpy scipy
```

## 运行程序

```bash
python main.py
```

---

## 串口数据协议 (高效版)

专为单片机设计的轻量级文本协议，高效且易于实现。

### 握手帧 (首次连接发送)

```
#H,<状态数>,<名称1>,<名称2>,...\n
```

**示例:**
```
#H,3,angle,position,force
#H,5,angle(rad),velocity(m/s),position(m),angular_vel(rad/s),control(N)
```

### 数据帧 (高频发送)

完整格式（包含目标值和当前值）:
```
#D,<序号>,<时间ms>,<目标1>,<当前1>,<目标2>,<当前2>,...\n
```

**示例:**
```
#D,1234,15000,0.00,0.05,0.00,-0.02,0.00,2.50
```

简化格式（仅当前值，目标值不变时使用）:
```
#d,<序号>,<时间ms>,<当前1>,<当前2>,...\n
```

**示例:**
```
#d,1234,15000,0.05,-0.02,2.50
```

### 旧格式兼容

仍然支持旧的键值对格式（自动生成默认状态定义）:
```
SP:100,PV:95.5,OUT:50
100,95.5,50
```

---

## 单片机示例代码 (Arduino)

## 项目结构

```
Control_System_Box/
├── main.py              # 程序入口
├── test_udp_sender.py   # UDP测试发送器 (协议 v2.0)
├── core/
│   ├── serial_manager.py    # 串口通信管理
│   ├── data_buffer.py       # 数据缓冲区
│   ├── simulator_receiver.py # UDP仿真数据接收 (协议 v2.0)
│   └── performance_analyzer.py  # 性能分析
├── ui/
│   ├── main_window.py       # 主窗口
│   ├── plot_widgets.py      # 绑图组件
│   ├── control_panel.py     # 控制面板
│   ├── unified_control_panel.py # 统一控制面板
│   ├── simulator_plot_widgets.py # 仿真图表组件
│   └── styles.py            # 样式定义
└── utils/
    └── simulator.py         # 模拟数据生成器
```

## UDP 仿真数据协议 (v2.0)

支持从物理仿真器接收实时数据，协议采用握手帧+数据帧分离设计。

### 握手帧 (HANDSHAKE)

```json
{
    "frame_type": "HANDSHAKE",
    "version": "2.0",
    "system_type": "inverted_pendulum",
    "state_count": 5,
    "states": [
        {"index": 0, "name": "position", "unit": "m", "description": "小车位置"},
        {"index": 1, "name": "velocity", "unit": "m/s", "description": "小车速度"},
        {"index": 2, "name": "angle", "unit": "rad", "description": "摆杆角度"},
        {"index": 3, "name": "angle_velocity", "unit": "rad/s", "description": "摆杆角速度"},
        {"index": 4, "name": "control_force", "unit": "N", "description": "控制力"}
    ]
}
```

### 数据帧 (DATA)

```json
{
    "frame_type": "DATA",
    "seq": 12345,
    "sim_time": 12.345,
    "state_count": 5,
    "states": [
        {"target": 0.0, "current": 0.05},
        {"target": 0.0, "current": -0.02},
        {"target": 0.0, "current": 0.03},
        {"target": 0.0, "current": 0.15},
        {"target": 0.0, "current": 2.5}
    ]
}
```

### 支持的仿真系统

- **倒立摆 (inverted_pendulum)**: 位置、速度、角度、角速度、控制力
- **滚球系统 (ball_on_plate)**: 球位置XY、球速度XY、平板角度XY

## 单片机端示例代码 (Arduino)

```cpp
// Arduino 串口数据发送示例
void loop() {
    float setpoint = 100.0;
    float processValue = readSensor();
    float output = pidControl(setpoint, processValue);
    
    // 发送数据到上位机
    Serial.print("SP:");
    Serial.print(setpoint);
    Serial.print(",PV:");
    Serial.print(processValue);
    Serial.print(",OUT:");
    Serial.println(output);
    
    delay(10);  // 100Hz 采样率
}

// 接收上位机命令
void serialEvent() {
    String cmd = Serial.readStringUntil('\n');
    
    if (cmd.startsWith("PID:")) {
        // 解析 PID:Kp,Ki,Kd
        // ...
    } else if (cmd.startsWith("SP:")) {
        // 解析新的设定值
        // ...
    }
}
```

## 许可证

MIT License
