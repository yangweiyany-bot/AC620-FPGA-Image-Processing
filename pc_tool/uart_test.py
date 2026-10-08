import serial
import time

ser = serial.Serial(
    port="COM13",
    baudrate=115200,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2
)

time.sleep(1)

# 清空以前残留的数据
ser.reset_input_buffer()

# 准备发送 4 个字节
send_data = bytes([0x55, 0xAA, 0x12, 0x34])

print("发送：", send_data.hex(" ").upper())

# 发送给 FPGA
ser.write(send_data)
ser.flush()

# 等 FPGA 返回 4 个字节
receive_data = ser.read(4)

print("接收：", receive_data.hex(" ").upper())

if receive_data == send_data:
    print("UART_LOOPBACK_PASS")
else:
    print("UART_LOOPBACK_FAIL")

ser.close()