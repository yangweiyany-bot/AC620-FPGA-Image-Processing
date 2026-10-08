from pathlib import Path
from PIL import Image
import numpy as np
import math

# ============================================================
# 文件路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

ORIGINAL_FILE = OUTPUT_DIR / "gray_256x256.png"
NOISY_FILE = OUTPUT_DIR / "noisy_256x256.png"

FPGA_MEAN_FILE = OUTPUT_DIR / "fpga_mean_3x3.bin"
FPGA_MEDIAN_FILE = OUTPUT_DIR / "fpga_median_3x3.bin"

MEAN_PNG = OUTPUT_DIR / "fpga_mean_noise_result.png"
MEDIAN_PNG = OUTPUT_DIR / "fpga_median_noise_result.png"


# ============================================================
# 读取原图、噪声图
# ============================================================

original = np.array(
    Image.open(ORIGINAL_FILE).convert("L"),
    dtype=np.uint8
)

noisy = np.array(
    Image.open(NOISY_FILE).convert("L"),
    dtype=np.uint8
)

if original.shape != (256, 256):
    raise ValueError("原始图片必须为 256x256")

if noisy.shape != (256, 256):
    raise ValueError("噪声图片必须为 256x256")


# ============================================================
# 读取 FPGA 输出
#
# 3x3 滤波后有效区域：
# 256 - 2 = 254
# 所以输出为 254 × 254
# ============================================================

mean_data = np.fromfile(FPGA_MEAN_FILE, dtype=np.uint8)
median_data = np.fromfile(FPGA_MEDIAN_FILE, dtype=np.uint8)

EXPECTED = 254 * 254

if len(mean_data) != EXPECTED:
    raise ValueError(
        f"均值滤波结果应该为 {EXPECTED} 字节，"
        f"实际为 {len(mean_data)}"
    )

if len(median_data) != EXPECTED:
    raise ValueError(
        f"中值滤波结果应该为 {EXPECTED} 字节，"
        f"实际为 {len(median_data)}"
    )

mean_img = mean_data.reshape(254, 254)
median_img = median_data.reshape(254, 254)


# ============================================================
# 保存 FPGA 输出图片
# ============================================================

Image.fromarray(mean_img).save(MEAN_PNG)
Image.fromarray(median_img).save(MEDIAN_PNG)


# ============================================================
# 对齐原图
#
# FPGA 的第一个输出对应原图 3x3 窗口的中心位置，
# 因此理论比较区域使用 original[1:-1, 1:-1]
# ============================================================

reference = original[1:-1, 1:-1]

# 同样取噪声图中心区域
noisy_crop = noisy[1:-1, 1:-1]


# ============================================================
# MSE / PSNR
# ============================================================

def mse(a, b):
    a = a.astype(np.float64)
    b = b.astype(np.float64)

    return np.mean((a - b) ** 2)


def psnr(a, b):
    value = mse(a, b)

    if value == 0:
        return float("inf")

    return 10 * math.log10((255.0 ** 2) / value)


# ============================================================
# 计算指标
# ============================================================

noisy_mse = mse(reference, noisy_crop)
mean_mse = mse(reference, mean_img)
median_mse = mse(reference, median_img)

noisy_psnr = psnr(reference, noisy_crop)
mean_psnr = psnr(reference, mean_img)
median_psnr = psnr(reference, median_img)


# ============================================================
# 输出
# ============================================================

print()
print("========== FPGA 滤波效果对比 ==========")
print()

print("                 MSE          PSNR")
print("-------------------------------------------")

print(
    f"椒盐噪声     {noisy_mse:10.4f}    "
    f"{noisy_psnr:8.4f} dB"
)

print(
    f"FPGA均值     {mean_mse:10.4f}    "
    f"{mean_psnr:8.4f} dB"
)

print(
    f"FPGA中值     {median_mse:10.4f}    "
    f"{median_psnr:8.4f} dB"
)

print()
print("FPGA均值结果图：", MEAN_PNG)
print("FPGA中值结果图：", MEDIAN_PNG)

print()
print("FILTER_EFFECT_COMPARE_PASS")
