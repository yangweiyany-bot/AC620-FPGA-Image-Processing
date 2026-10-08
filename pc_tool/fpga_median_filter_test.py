import serial
import time
from pathlib import Path

# ============================================================
# 参数
# ============================================================

PORT = "COM13"
BAUD = 115200

WIDTH = 256
HEIGHT = 256

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "gray_256x256.bin"
OUTPUT_FILE = OUTPUT_DIR / "fpga_median_3x3.bin"

INPUT_BYTES = WIDTH * HEIGHT          # 65536
OUTPUT_WIDTH = WIDTH - 2              # 254
OUTPUT_HEIGHT = HEIGHT - 2            # 254
EXPECTED_OUTPUT = OUTPUT_WIDTH * OUTPUT_HEIGHT   # 64516


# ============================================================
# 读取灰度图二进制数据
# ============================================================

image_data = INPUT_FILE.read_bytes()

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

# 清空以前可能残留的数据
ser.reset_input_buffer()
ser.reset_output_buffer()

print()
print("串口已打开：", PORT)
print("开始发送图片……")


# ============================================================
# 发送图片
# ============================================================

start_time = time.time()

received = bytearray()

for i, pixel in enumerate(image_data):

    # 发送一个灰度像素
    ser.write(bytes([pixel]))
    ser.flush()

    # 给 FPGA UART 足够的发送时间
    time.sleep(0.00015)

    # 读取 FPGA 已返回的数据
    waiting = ser.in_waiting

    if waiting > 0:
        data = ser.read(waiting)
        received.extend(data)

    # 每发送 4096 字节显示一次进度
    if (i + 1) % 4096 == 0:
        print(
            f"发送进度：{i + 1}/{INPUT_BYTES}，"
            f"已接收：{len(received)}/{EXPECTED_OUTPUT}"
        )


# ============================================================
# 等待 FPGA 把最后的数据发完
# ============================================================

print()
print("图片发送完成，等待最后的 FPGA 数据……")

deadline = time.time() + 5

while len(received) < EXPECTED_OUTPUT and time.time() < deadline:

    waiting = ser.in_waiting

    if waiting > 0:
        received.extend(ser.read(waiting))
    else:
        time.sleep(0.01)


ser.close()

elapsed = time.time() - start_time


# ============================================================
# 检查结果
# ============================================================

print()
print("========== FPGA 中值滤波处理结果 ==========")

print("发送字节数：", len(image_data))
print("接收字节数：", len(received))
print("理论字节数：", EXPECTED_OUTPUT)
print(f"总耗时：{elapsed:.2f} 秒")


if len(received) == EXPECTED_OUTPUT:

    print("FPGA_MEDIAN_FILTER_TRANSFER_PASS")

    OUTPUT_FILE.write_bytes(received)

    print("结果已保存：", OUTPUT_FILE)

else:

    print("FPGA_MEDIAN_FILTER_TRANSFER_FAIL")

    print(
        "缺少字节：",
        EXPECTED_OUTPUT - len(received)
    )
