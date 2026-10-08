import serial
import time
from pathlib import Path

# =========================
# 参数
# =========================
PORT = "COM13"
BAUD = 115200

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGE_FILE = OUTPUT_DIR / "gray_256x256.bin"

# =========================
# 读取图片二进制数据
# =========================
image_data = IMAGE_FILE.read_bytes()

print("文件：", IMAGE_FILE)
print("数据大小：", len(image_data), "bytes")

if len(image_data) != 256 * 256:
    raise ValueError(
        f"文件大小错误：应该是 65536 bytes，实际是 {len(image_data)} bytes"
    )

# =========================
# 打开串口
# =========================
ser = serial.Serial(
    port=PORT,
    baudrate=BAUD,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=10
)

time.sleep(1)

ser.reset_input_buffer()
ser.reset_output_buffer()

print("开始发送图片...")

start_time = time.time()

# =========================
# 分块发送
# =========================
received = bytearray()

CHUNK_SIZE = 256

for i in range(0, len(image_data), CHUNK_SIZE):

    chunk = image_data[i:i + CHUNK_SIZE]

    ser.write(chunk)
    ser.flush()

    # FPGA目前是UART回环程序，
    # 所以发送多少，就等待返回多少
    echo = ser.read(len(chunk))
    received.extend(echo)

    current = min(i + CHUNK_SIZE, len(image_data))

    print(
        f"\r进度：{current}/{len(image_data)} bytes "
        f"({current / len(image_data) * 100:.1f}%)",
        end=""
    )

print()

end_time = time.time()

ser.close()

# =========================
# 验证
# =========================
print("发送完成")
print("发送字节数：", len(image_data))
print("接收字节数：", len(received))
print(f"耗时：{end_time - start_time:.2f} 秒")

if bytes(received) == image_data:
    print("IMAGE_UART_LOOPBACK_PASS")
else:
    print("IMAGE_UART_LOOPBACK_FAIL")
