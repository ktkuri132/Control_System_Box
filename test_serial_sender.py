"""
串口协议测试发送器
模拟单片机发送数据，用于测试新的串口协议
可通过虚拟串口（如 com0com）或实际串口测试
"""

import serial
import time
import math
import random
import argparse


def generate_pendulum_data(t: float) -> tuple:
    """生成倒立摆模拟数据"""
    omega = 2.5  # 自然频率
    zeta = 0.3   # 阻尼比

    # 带阻尼的振荡响应
    angle = 0.15 * math.exp(-zeta * omega * t) * math.cos(omega * math.sqrt(1 - zeta**2) * t)
    angular_velocity = -0.15 * omega * math.exp(-zeta * omega * t) * math.sin(omega * math.sqrt(1 - zeta**2) * t)

    # 小车位置
    cart_position = -0.3 * angle + 0.02 * math.sin(0.5 * t)

    # 控制力
    control_force = -15.0 * angle - 5.0 * angular_velocity - 2.0 * cart_position

    # 添加噪声
    angle += random.gauss(0, 0.001)
    cart_position += random.gauss(0, 0.001)

    # 目标值 (都是0，保持平衡)
    return [
        (0.0, angle),           # angle: target, current
        (0.0, cart_position),   # position: target, current
        (0.0, control_force),   # force: target, current
    ]


def generate_ball_data(t: float) -> tuple:
    """生成滚球模拟数据"""
    # 目标轨迹 - 圆形
    target_x = 0.05 * math.cos(0.5 * t)
    target_y = 0.05 * math.sin(0.5 * t)

    # 实际位置 - 带滞后
    delay = 0.3
    damping = 0.7
    actual_x = 0.05 * math.cos(0.5 * (t - delay)) * (1 - math.exp(-damping * t))
    actual_y = 0.05 * math.sin(0.5 * (t - delay)) * (1 - math.exp(-damping * t))

    # 添加噪声
    actual_x += random.gauss(0, 0.002)
    actual_y += random.gauss(0, 0.002)

    # 平板角度
    error_x = target_x - actual_x
    error_y = target_y - actual_y
    plate_x = -0.1 * error_x
    plate_y = -0.1 * error_y

    return [
        (target_x * 1000, actual_x * 1000),  # ball_x (mm)
        (target_y * 1000, actual_y * 1000),  # ball_y (mm)
        (0.0, plate_x * 57.3),               # plate_angle_x (deg)
        (0.0, plate_y * 57.3),               # plate_angle_y (deg)
    ]


def send_handshake(ser, system_type: str):
    """发送握手帧"""
    if system_type == 'pendulum':
        line = "#H,3,angle(rad),position(m),force(N)\n"
    else:
        line = "#H,4,ball_x(mm),ball_y(mm),plate_x(deg),plate_y(deg)\n"

    ser.write(line.encode('utf-8'))
    print(f"[HANDSHAKE] {line.strip()}")


def send_data_full(ser, seq: int, time_ms: int, states: list):
    """发送完整数据帧"""
    values = []
    for target, current in states:
        values.append(f"{target:.4f}")
        values.append(f"{current:.4f}")
    line = f"#D,{seq},{time_ms},{','.join(values)}\n"
    ser.write(line.encode('utf-8'))
    return line


def send_data_simple(ser, seq: int, time_ms: int, states: list):
    """发送简化数据帧"""
    values = [f"{current:.4f}" for _, current in states]
    line = f"#d,{seq},{time_ms},{','.join(values)}\n"
    ser.write(line.encode('utf-8'))
    return line


def main():
    parser = argparse.ArgumentParser(description='串口协议测试发送器')
    parser.add_argument('--port', '-p', default='COM3', help='串口端口')
    parser.add_argument('--baud', '-b', type=int, default=115200, help='波特率')
    parser.add_argument('--rate', '-r', type=int, default=100, help='发送频率 (Hz)')
    parser.add_argument('--system', '-s', choices=['pendulum', 'ball'], default='pendulum',
                        help='系统类型: pendulum=倒立摆, ball=滚球')
    parser.add_argument('--simple', action='store_true', help='使用简化数据帧')
    args = parser.parse_args()

    print("=" * 60)
    print("串口协议测试发送器")
    print("=" * 60)
    print(f"端口: {args.port}")
    print(f"波特率: {args.baud}")
    print(f"频率: {args.rate} Hz")
    print(f"系统: {args.system}")
    print(f"帧格式: {'简化' if args.simple else '完整'}")
    print("-" * 60)

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"已打开 {args.port}")
    except serial.SerialException as e:
        print(f"无法打开串口: {e}")
        print("\n提示: 可以使用 com0com 创建虚拟串口对进行测试")
        return

    # 发送握手帧
    send_handshake(ser, args.system)

    start_time = time.time()
    seq = 0
    last_targets = None

    print("开始发送数据... (按 Ctrl+C 停止)")

    try:
        while True:
            t = time.time() - start_time
            time_ms = int(t * 1000)

            # 生成数据
            if args.system == 'pendulum':
                states = generate_pendulum_data(t)
            else:
                states = generate_ball_data(t)

            # 发送数据
            if args.simple and last_targets is not None:
                # 检查目标值是否改变
                targets_changed = any(
                    abs(states[i][0] - last_targets[i]) > 0.001
                    for i in range(len(states))
                )
                if targets_changed:
                    line = send_data_full(ser, seq, time_ms, states)
                else:
                    line = send_data_simple(ser, seq, time_ms, states)
            else:
                line = send_data_full(ser, seq, time_ms, states)

            last_targets = [s[0] for s in states]
            seq += 1

            # 定期打印状态
            if seq % 100 == 0:
                if args.system == 'pendulum':
                    print(f"[{seq}] t={t:.1f}s | 角度: {states[0][1]*57.3:+.2f}° | 力: {states[2][1]:+.1f}N")
                else:
                    err = math.sqrt((states[0][0]-states[0][1])**2 + (states[1][0]-states[1][1])**2)
                    print(f"[{seq}] t={t:.1f}s | 误差: {err:.1f}mm")

            # 控制发送频率
            time.sleep(1.0 / args.rate)

    except KeyboardInterrupt:
        print(f"\n停止. 共发送 {seq} 帧")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
