from pathlib import Path
import numpy as np
from PIL import Image

# ============================================================
# 文件
# ============================================================

WIDTH = 256
HEIGHT = 256

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "gray_256x256.bin"
FPGA_FILE = OUTPUT_DIR / "fpga_median_3x3.bin"

FPGA_IMAGE_FILE = OUTPUT_DIR / "fpga_median_3x3.png"
REFERENCE_IMAGE_FILE = OUTPUT_DIR / "median_fpga_reference.png"
DIFF_IMAGE_FILE = OUTPUT_DIR / "median_difference.png"


# ============================================================
# 读取原始图像
# ============================================================

raw = INPUT_FILE.read_bytes()

if len(raw) != WIDTH * HEIGHT:
    raise ValueError(
        f"原图应该为 {WIDTH * HEIGHT} 字节，"
        f"实际为 {len(raw)} 字节"
    )

image = np.frombuffer(raw, dtype=np.uint8).reshape(HEIGHT, WIDTH)


# ============================================================
# 读取 FPGA 实际输出
# ============================================================

fpga_raw = FPGA_FILE.read_bytes()

EXPECTED = (WIDTH - 2) * (HEIGHT - 2)

if len(fpga_raw) != EXPECTED:
    raise ValueError(
        f"FPGA结果应该为 {EXPECTED} 字节，"
        f"实际为 {len(fpga_raw)} 字节"
    )

fpga = np.frombuffer(
    fpga_raw,
    dtype=np.uint8
).reshape(HEIGHT - 2, WIDTH - 2)


# ============================================================
# 严格按照 median_filter_3x3.v 模拟
# ============================================================

reference = np.zeros(
    (HEIGHT - 2, WIDTH - 2),
    dtype=np.uint8
)

for row in range(2, HEIGHT):

    for col in range(2, WIDTH):

        # 对应 Verilog 中：
        #
        # p00, p01, line2[col]
        # p10, p11, line1[col]
        # line1[col-2], line1[col-1], pixel_in
        #
        # 在正常逐行输入的情况下，对应标准3×3窗口：

        window = [
            image[row - 2, col - 2],
            image[row - 2, col - 1],
            image[row - 2, col],

            image[row - 1, col - 2],
            image[row - 1, col - 1],
            image[row - 1, col],

            image[row, col - 2],
            image[row, col - 1],
            image[row, col]
        ]

        window.sort()

        # Verilog median9 = a[4]
        reference[row - 2, col - 2] = window[4]


# ============================================================
# 比较
# ============================================================

fpga_i = fpga.astype(np.int16)
ref_i = reference.astype(np.int16)

diff = fpga_i - ref_i
abs_diff = np.abs(diff)

same = np.sum(diff == 0)
total = diff.size

accuracy = same / total * 100

max_error = np.max(abs_diff)
mae = np.mean(abs_diff)


print()
print("========== FPGA 中值滤波严格验证 ==========")

print("比较像素数：", total)
print("完全相同像素：", same)
print(f"完全一致率：{accuracy:.4f}%")
print("最大误差：", max_error)
print("MAE：", mae)


# ============================================================
# 保存图像
# ============================================================

Image.fromarray(fpga).save(FPGA_IMAGE_FILE)
Image.fromarray(reference).save(REFERENCE_IMAGE_FILE)

# 差异图放大，方便肉眼观察
diff_image = np.clip(abs_diff * 4, 0, 255).astype(np.uint8)
Image.fromarray(diff_image).save(DIFF_IMAGE_FILE)

print()
print("FPGA结果图：", FPGA_IMAGE_FILE)
print("理论参考图：", REFERENCE_IMAGE_FILE)
print("差异图：", DIFF_IMAGE_FILE)


# ============================================================
# 最终判断
# ============================================================

if max_error == 0:

    print()
    print("FPGA_MEDIAN_FILTER_RESULT_EXACT_MATCH")

else:

    print()
    print("FPGA_MEDIAN_FILTER_RESULT_MISMATCH")

    # 找出前20个不同的位置
    positions = np.argwhere(diff != 0)

    print()
    print("前20个不同像素：")

    for r, c in positions[:20]:

        print(
            f"[{r:3d},{c:3d}] "
            f"FPGA={fpga[r, c]:3d}  "
            f"理论={reference[r, c]:3d}  "
            f"差={diff[r, c]:+d}"
        )
