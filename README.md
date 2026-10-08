# 基于 AC620 FPGA 的 UART 图像均值与中值滤波系统

## 项目简介

本项目在 AC620 V2 开发板上实现 8 bit 灰度图像的实时流式滤波。Python 上位机通过 UART 向 FPGA 发送算法选择命令和 `256×256` 灰度图像；FPGA 使用两级行缓存构造 `3×3` 窗口，完成均值滤波或中值滤波，再将 `254×254` 的有效结果通过 UART 返回上位机进行保存、逐像素验证和效果分析。

已实现功能：

- UART 接收与发送，波特率 `115200`，格式为 8N1；
- `AA 55 00` 选择 `3×3` 均值滤波；
- `AA 55 01` 选择 `3×3` 中值滤波；
- `256×256`、8 bit 灰度图像预处理和二进制生成；
- FPGA 输出接收及 `254×254` 图像重建；
- 均值、中值滤波的软件参考模型和逐像素比较；
- 固定随机种子的椒盐噪声生成，以及 MSE、PSNR 效果对比；
- UART 字节回环和整幅图像回环辅助测试脚本；
- 均值、中值滤波 RTL Testbench。

## 系统工作流程

```text
Python读取图片
      ↓
缩放并转换为256×256灰度图
      ↓
发送算法命令AA 55 00或AA 55 01
      ↓
通过UART发送65536个灰度像素
      ↓
FPGA接收并利用行缓存构造3×3窗口
      ↓
执行均值滤波或中值滤波
      ↓
通过UART返回64516个有效像素
      ↓
Python保存254×254结果并与参考结果比较
```

### UART 命令

| 命令 | 功能 |
|---|---|
| `AA 55 00` | 选择 `3×3` 均值滤波 |
| `AA 55 01` | 选择 `3×3` 中值滤波 |

命令之后紧跟 `256×256 = 65536` 个按行排列的 8 bit 灰度像素，不包含额外的宽度、长度或校验字段。FPGA 收满一帧后退出图像接收状态，等待下一条命令。

## 仓库结构

```text
AC620-FPGA-Image-Processing/
├── README.md
├── fpga/
│   ├── rtl/
│   │   ├── ac620_uart_loopback_top.v
│   │   ├── uart_rx.v
│   │   ├── uart_tx.v
│   │   ├── mean_filter_3x3.v
│   │   └── median_filter_3x3.v
│   ├── tb/
│   │   ├── tb_uart_loopback.v
│   │   ├── tb_mean_filter_3x3.v
│   │   └── tb_median_filter_3x3.v
│   └── quartus/
│       ├── ac620_uart_loopback.qpf
│       ├── ac620_uart_loopback.qsf
│       └── ac620_uart_loopback.sdc
└── pc_tool/
    ├── image_tool.py
    ├── make_noise_image.py
    ├── fpga_filter_test.py
    ├── fpga_mean_filter_test.py
    ├── fpga_median_filter_test.py
    ├── compare_fpga_result.py
    ├── compare_fpga_median_result.py
    ├── compare_filter_effect.py
    ├── uart_test.py
    ├── uart_image_test.py
    └── requirements.txt
```

主要文件说明：

| 文件 | 作用 |
|---|---|
| `ac620_uart_loopback_top.v` | 顶层模块、命令解析、算法选择和 UART 结果调度 |
| `uart_rx.v` / `uart_tx.v` | UART 8N1 接收与发送模块 |
| `mean_filter_3x3.v` | `3×3` 均值滤波及行缓存 |
| `median_filter_3x3.v` | `3×3` 中值滤波及行缓存 |
| `image_tool.py` | 输入图片缩放、灰度化、BIN文件及软件参考图生成 |
| `make_noise_image.py` | 生成固定种子的5%椒盐噪声图和BIN文件 |
| `fpga_filter_test.py` | 当前统一协议的均值/中值滤波串口测试入口 |
| `compare_fpga_result.py` | 均值滤波结果的逐像素验证与差异图生成 |
| `compare_fpga_median_result.py` | 中值滤波结果的逐像素验证与差异图生成 |
| `compare_filter_effect.py` | 原图、噪声图、均值结果和中值结果的 MSE/PSNR 对比 |

`fpga_mean_filter_test.py` 和 `fpga_median_filter_test.py` 只发送像素数据，不发送 `AA 55 XX` 命令，保留用于相应的独立固定滤波配置。当前统一顶层应使用 `fpga_filter_test.py`。`uart_test.py` 和 `uart_image_test.py` 用于 UART 回环配置，不用于当前滤波顶层。

## 硬件与软件环境

### 硬件

| 项目 | 规格 |
|---|---|
| 开发板 | AC620 V2 |
| FPGA | Altera Cyclone IV E `EP4CE10F17C8` |
| 系统时钟 | 50 MHz |
| 下载接口 | USB-Blaster / JTAG |
| 数据通信 | 板载 USB-UART |

主要引脚分配：

| 信号 | 引脚 | 说明 |
|---|---|---|
| `clk` | `PIN_E1` | 50 MHz 时钟 |
| `rst_n` | `PIN_E16` | S2，低电平复位 |
| `led` | `PIN_A2` | LED0，低电平点亮 |
| `uart_rx` | `PIN_B5` | FPGA UART 接收 |
| `uart_tx` | `PIN_A6` | FPGA UART 发送 |

### 软件

- Windows；
- Quartus II 13.0 64-bit；
- Python 3.13；
- Python依赖：NumPy、Pillow、pySerial。

## Quartus 工程

### 打开和编译

1. 启动 Quartus II 13.0。
2. 选择 `File → Open Project`。
3. 打开：

   ```text
   fpga/quartus/ac620_uart_loopback.qpf
   ```

4. 确认器件为 `EP4CE10F17C8`，顶层实体为 `ac620_uart_loopback_top`。
5. 选择 `Processing → Start Compilation`。

也可以在 `fpga/quartus` 目录执行：

```powershell
quartus_sh --flow compile ac620_uart_loopback
```

编译生成的 `db/`、`incremental_db/`、`output_files/` 和 `simulation/modelsim/` 为本地产物，已通过 `.gitignore` 排除。

### 下载到开发板

1. 给开发板供电并连接 USB-Blaster。
2. 在 Quartus 中选择 `Tools → Programmer`。
3. 在 `Hardware Setup` 中选择 `USB-Blaster [USB-0]`，模式选择 `JTAG`。
4. 添加编译生成的文件：

   ```text
   fpga/quartus/output_files/ac620_uart_loopback.sof
   ```

5. 勾选 `Program/Configure`，点击 `Start`，等待进度达到100%。

`.sof` 为易失配置，开发板断电后需要重新下载。

## Python 上位机

以下命令均在仓库根目录执行。

### 1. 安装依赖

```powershell
python -m pip install -r pc_tool/requirements.txt
```

也可以使用题目要求的简写：

```powershell
pip install -r pc_tool/requirements.txt
```

### 2. 准备输入图像

创建本地输入目录，并放入一张 `.jpg`、`.jpeg`、`.png` 或 `.bmp` 图片：

```powershell
New-Item -ItemType Directory -Force pc_tool/input
```

运行预处理：

```powershell
python pc_tool/image_tool.py
```

脚本读取 `pc_tool/input/` 中找到的第一张图片，并生成：

```text
pc_tool/output/gray_256x256.png
pc_tool/output/gray_256x256.bin
pc_tool/output/mean_3x3_reference.png
pc_tool/output/median_3x3_reference.png
```

`gray_256x256.bin` 为按行排列的65536个灰度字节。

### 3. 生成噪声测试图

当前统一滤波脚本默认读取 `pc_tool/output/noisy_256x256.bin`，因此先运行：

```powershell
python pc_tool/make_noise_image.py
```

该脚本在灰度图中加入5%椒盐噪声，随机种子固定为 `2026`，生成：

```text
pc_tool/output/noisy_256x256.png
pc_tool/output/noisy_256x256.bin
```

### 4. 设置串口号

打开 `pc_tool/fpga_filter_test.py`，根据 Windows 设备管理器中的实际端口修改：

```python
PORT = "COM13"
```

脚本默认值为 `COM13`。串口参数固定为：

```text
115200 baud，8 data bits，no parity，1 stop bit
```

运行前应关闭串口助手等占用该端口的软件。

### 5. 执行滤波测试

确认 FPGA 已下载当前工程的 `.sof`，然后执行：

```powershell
python pc_tool/fpga_filter_test.py
```

脚本提示选择模式：

```text
0 - 3x3 均值滤波，发送 AA 55 00
1 - 3x3 中值滤波，发送 AA 55 01
```

默认输入文件：

```text
pc_tool/output/noisy_256x256.bin
```

对应输出文件：

```text
模式0：pc_tool/output/fpga_mean_3x3.bin
模式1：pc_tool/output/fpga_median_3x3.bin
```

每次运行处理一种算法。若需要进行效果对比，应分别运行模式0和模式1，确保两个输出文件都已生成。

### 6. 结果可视化与效果对比

当均值和中值结果均已生成后执行：

```powershell
python pc_tool/compare_filter_effect.py
```

该脚本读取原始灰度图、噪声图和两个 FPGA 输出，生成对应 PNG，并输出 MSE 和 PSNR。

若要重新进行无噪声图的逐像素一致性验证，可将 `fpga_filter_test.py` 中的输入改为：

```python
INPUT_FILE = OUTPUT_DIR / "gray_256x256.bin"
```

分别运行模式0和模式1后执行：

```powershell
python pc_tool/compare_fpga_result.py
python pc_tool/compare_fpga_median_result.py
```

这两个比较脚本分别验证均值和中值滤波输出，并生成结果图、参考图和差异图。

## 滤波原理

### `3×3` 均值滤波

对当前 `3×3` 邻域内的9个灰度值求和并进行整数除法：

```text
y = (p00 + p01 + p02 + p10 + p11 + p12 + p20 + p21 + p22) / 9
```

均值滤波可以平滑局部灰度变化并抑制一般随机噪声，但也可能使边缘和细节变模糊。

### `3×3` 中值滤波

将当前 `3×3` 邻域的9个灰度值排序，取排序后的第5个值作为输出。中值滤波属于非线性滤波，对椒盐噪声通常具有较好的抑制能力，同时比均值滤波更容易保留边缘。

FPGA 使用两行历史像素缓存与当前行移位寄存器构造窗口，不需要缓存完整图像。

## 输入与输出尺寸

本工程不对图像边界进行填充，只输出具有完整 `3×3` 邻域的位置。因此每个方向减少2个像素：

```text
输入：256 × 256 = 65536 bytes
输出：(256 - 2) × (256 - 2)
    = 254 × 254
    = 64516 bytes
```

输出尺寸不同是有效窗口滤波的预期结果，不是串口丢包。

## 已完成验证

- Quartus II 13.0 可以完整读取仓库中的 QPF、QSF、SDC、RTL 和 Testbench 文件；
- 工程完整编译结果为 `0 errors`，并可生成 `.sof`；
- UART基础回环和图像数据传输流程已完成验证；
- 此前的逐像素测试中，均值滤波输出与软件参考结果一致，`MAE = 0`；
- 此前的逐像素测试中，中值滤波输出与软件参考结果一致，`MAE = 0`。

上述逐像素测试输出属于本地实验数据，不纳入Git版本控制。

## 已知问题

Quartus 虽然能够完成编译并生成编程文件，但当前设计尚未满足50 MHz时序要求。最近一次编译报告的最差 setup slack 为：

```text
-26.676 ns
```

TimeQuest 报告 `Timing requirements not met`。因此不能声称时序已经收敛；后续需要对滤波数据通路进行流水化、资源优化或重新评估时钟约束。

编译还存在HDL推断、I/O分配和器件接口方面的警告，使用前应结合 Quartus 报告继续检查。

## 本地数据目录

以下目录由脚本在本地使用，不纳入Git版本控制：

```text
pc_tool/input/   # 用户输入图片
pc_tool/output/  # 灰度图、BIN、FPGA返回结果和比较图
```

克隆仓库后目录不存在属于正常情况，运行 `image_tool.py` 会自动创建它们。

## 常见问题

### 提示找不到输入文件

先在 `pc_tool/input/` 放入图片并运行：

```powershell
python pc_tool/image_tool.py
```

默认滤波测试还需要运行 `make_noise_image.py` 生成 `noisy_256x256.bin`。

### 串口无法打开

检查设备管理器中的实际 COM 号，修改 `fpga_filter_test.py` 的 `PORT`，并关闭正在占用该端口的串口助手。

### 收到的数据不是64516字节

检查波特率是否为115200、FPGA是否下载了当前滤波工程、命令是否为 `AA 55 00/01`、输入文件是否恰好为65536字节，并确认传输期间没有复位或断电。

### 为什么不直接使用两个独立滤波测试脚本

当前统一顶层在收到 `AA 55 XX` 后才进入图像接收状态。`fpga_mean_filter_test.py` 和 `fpga_median_filter_test.py` 不发送命令头，因此当前工程应使用 `fpga_filter_test.py`。
