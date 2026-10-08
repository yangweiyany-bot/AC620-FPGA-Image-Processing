import serial
import time
from pathlib import Path

# ============================================================
# 基本参数
# ============================================================

PORT = "COM13"
BAUD = 115200

WIDTH = 256
HEIGHT = 256

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "noisy_256x256.bin"

INPUT_BYTES = WIDTH * HEIGHT

OUTPUT_WIDTH = WIDTH - 2
OUTPUT_HEIGHT = HEIGHT - 2
EXPECTED_OUTPUT = OUTPUT_WIDTH * OUTPUT_HEIGHT


# ============================================================
# 选择滤波模式
# ============================================================

print()
print("========== FPGA 图像滤波测试 ==========")
print()
print("0 - 3x3 均值滤波")
print("1 - 3x3 中值滤波")
print()

mode = input("请输入模式（0/1）：").strip()

if mode == "0":

    command = bytes([0xAA, 0x55, 0x00])

    OUTPUT_FILE = OUTPUT_DIR / "fpga_mean_3x3.bin"

    filter_name = "3x3 均值滤波"

elif mode == "1":

    command = bytes([0xAA, 0x55, 0x01])

    OUTPUT_FILE = OUTPUT_DIR / "fpga_median_3x3.bin"

    filter_name = "3x3 中值滤波"

else:

    raise ValueError("模式只能输入 0 或 1")


# ============================================================
# 读取输入图像
# ============================================================

image_data = INPUT_FILE.read_bytes()

print()
print("选择模式：", filter_name)
print("输入文件：", INPUT_FILE)
print("输入字节数：", len(image_data))

if len(image_data) != INPUT_BYTES:

    raise ValueError(
        f"输入文件应该为 {INPUT_BYTES} 字节，"
        f"实际为 {len(image_data)} 字节"
    )


# ============================================================
# 打开串口
# ============================================================

ser = serial.Serial(
    port=PORT,
    baudrate=BAUD,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2
)

time.sleep(0.5)

ser.reset_input_buffer()
ser.reset_output_buffer()

print()
print("串口已打开：", PORT)


# ============================================================
# 发送滤波命令
# ============================================================

print("发送滤波命令……")

ser.write(command)
ser.flush()

# 稍微等待 FPGA 完成命令解析
time.sleep(0.05)

print(
    "命令：",
    " ".join(f"{b:02X}" for b in command)
)

print()
print("开始发送图片……")


# ============================================================
# 发送图片并同时接收 FPGA 结果
# ============================================================

start_time = time.time()

received = bytearray()

for i, pixel in enumerate(image_data):

    # 发送一个像素
    ser.write(bytes([pixel]))
    ser.flush()

    # 给 UART TX 留足够时间
    time.sleep(0.00015)

    # 接收 FPGA 已经产生的数据
    waiting = ser.in_waiting

    if waiting > 0:

        data = ser.read(waiting)

        received.extend(data)

    # 显示进度
    if (i + 1) % 4096 == 0:

        print(
            f"发送进度：{i + 1}/{INPUT_BYTES}，"
            f"已接收：{len(received)}/{EXPECTED_OUTPUT}"
        )


# ============================================================
# 等待最后剩余的数据
# ============================================================

print()
print("图片发送完成，等待 FPGA 最后的数据……")

deadline = time.time() + 5

while (
    len(received) < EXPECTED_OUTPUT
    and time.time() < deadline
):

    waiting = ser.in_waiting

    if waiting > 0:

        received.extend(
            ser.read(waiting)
        )

    else:

        time.sleep(0.01)


ser.close()

elapsed = time.time() - start_time


# ============================================================
# 输出结果
# ============================================================

print()
print("========== FPGA 处理结果 ==========")

print("滤波模式：", filter_name)

print("发送字节数：", len(image_data))

print("接收字节数：", len(received))

print("理论字节数：", EXPECTED_OUTPUT)

print(f"总耗时：{elapsed:.2f} 秒")


# ============================================================
# 判断传输是否成功
# ============================================================

if len(received) == EXPECTED_OUTPUT:

    print()
    print("FPGA_FILTER_TRANSFER_PASS")

    OUTPUT_FILE.write_bytes(received)

    print("结果已保存：", OUTPUT_FILE)

else:

    print()
    print("FPGA_FILTER_TRANSFER_FAIL")

    print(
        "缺少字节：",
        EXPECTED_OUTPUT - len(received)
    )
