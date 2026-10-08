from pathlib import Path
import numpy as np
from PIL import Image

# ============================================================
# 文件路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

FPGA_FILE = OUTPUT_DIR / "fpga_mean_3x3.bin"
REFERENCE_FILE = OUTPUT_DIR / "mean_3x3_reference.png"

FPGA_IMAGE_FILE = OUTPUT_DIR / "fpga_mean_3x3.png"
DIFF_IMAGE_FILE = OUTPUT_DIR / "difference.png"
GRAY_IMAGE_FILE = OUTPUT_DIR / "gray_256x256.png"

WIDTH = 254
HEIGHT = 254


# ============================================================
# 1. 读取 FPGA 返回的二进制数据
# ============================================================

fpga_data = FPGA_FILE.read_bytes()

print("FPGA 数据字节数：", len(fpga_data))

if len(fpga_data) != WIDTH * HEIGHT:
    raise ValueError(
        f"FPGA 数据应该为 {WIDTH * HEIGHT} 字节，"
        f"实际为 {len(fpga_data)} 字节"
    )

fpga_array = np.frombuffer(
    fpga_data,
    dtype=np.uint8
).reshape((HEIGHT, WIDTH))


# ============================================================
# 2. 保存 FPGA 结果图片
# ============================================================

fpga_image = Image.fromarray(fpga_array, mode="L")
fpga_image.save(FPGA_IMAGE_FILE)

print("FPGA结果图已保存：", FPGA_IMAGE_FILE)


# ============================================================
# 3. 读取 Python 参考结果
# ============================================================

reference = Image.open(REFERENCE_FILE).convert("L")
reference_array = np.array(reference)

print("参考图尺寸：", reference_array.shape)


# ============================================================
# 4. 处理尺寸
#
# FPGA只输出具有完整3×3邻域的位置，
# 所以结果是254×254。
# ============================================================

if reference_array.shape == (256, 256):

    reference_array = reference_array[2:, 2:]

elif reference_array.shape != (254, 254):

    raise ValueError(
        f"参考图尺寸异常：{reference_array.shape}"
    )


# ============================================================
# 5. FPGA 与 Python 逐像素比较
# ============================================================

fpga_int = fpga_array.astype(np.int16)
ref_int = reference_array.astype(np.int16)

difference = fpga_int - ref_int
abs_difference = np.abs(difference)

max_error = abs_difference.max()
mae = abs_difference.mean()

same_pixels = np.sum(abs_difference == 0)
total_pixels = WIDTH * HEIGHT

same_ratio = same_pixels / total_pixels * 100


print()
print("========== FPGA / Python 对比 ==========")

print("比较像素数：", total_pixels)
print("完全相同像素：", same_pixels)
print(f"完全一致率：{same_ratio:.4f}%")
print("最大像素误差：", max_error)
print(f"平均绝对误差 MAE：{mae:.6f}")


# ============================================================
# 6. 保存差异图
# ============================================================

diff_display = np.clip(
    abs_difference,
    0,
    255
).astype(np.uint8)

Image.fromarray(
    diff_display,
    mode="L"
).save(DIFF_IMAGE_FILE)

print()
print("差异图已保存：", DIFF_IMAGE_FILE)


# ============================================================
# 7. 最终判断
# ============================================================

if max_error == 0:

    print()
    print("FPGA_MEAN_FILTER_RESULT_EXACT_MATCH")

else:

    print()
    print("FPGA_MEAN_FILTER_RESULT_MISMATCH")
    print("\n========== 前20个像素检查 ==========")

    for i in range(20):
        r = i // 254
        c = i % 254

        print(
            f"[{r:3d},{c:3d}] "
            f"FPGA={fpga_array[r, c]:3d}   "
            f"Python={reference_array[r, c]:3d}   "
            f"差={int(fpga_array[r, c]) - int(reference_array[r, c]):+d}"
        )
        print("\n========== 自动搜索最佳空间对齐 ==========")

        original = np.array(
            Image.open(GRAY_IMAGE_FILE).convert("L")
        ).astype(np.int16)

        best_mae = 999999
        best_offset = None

        for dr in range(0, 3):
            for dc in range(0, 3):

                # 从原图取对应区域
                region = original[
                    dr:dr + 254,
                    dc:dc + 254
                ]

                mae_test = np.mean(
                    np.abs(fpga_int - region)
                )

                print(
                    f"偏移 ({dr},{dc})："
                    f"MAE = {mae_test:.4f}"
                )

                if mae_test < best_mae:
                    best_mae = mae_test
                    best_offset = (dr, dc)

        print()
        print("最佳偏移：", best_offset)
        print("最佳 MAE：", best_mae)
        print("\n========== 严格模拟 FPGA 的 3×3 均值计算 ==========")

        original = np.array(
            Image.open(GRAY_IMAGE_FILE).convert("L")
        ).astype(np.int32)

        fpga_reference = np.zeros((254, 254), dtype=np.int32)

        for r in range(254):
            for c in range(254):
                window = original[
                    r:r + 3,
                    c:c + 3
                ]

                # Verilog整数除法：直接舍弃小数部分
                fpga_reference[r, c] = int(window.sum()) // 9

        # 和 FPGA 真正返回的数据比较
        error = fpga_array.astype(np.int32) - fpga_reference

        abs_error = np.abs(error)

        print("比较像素数：", 254 * 254)
        print("完全相同像素：", np.sum(abs_error == 0))
        print(
            "完全一致率：",
            f"{np.mean(abs_error == 0) * 100:.4f}%"
        )

        print("最大误差：", abs_error.max())
        print("MAE：", abs_error.mean())

        print("\n========== 前20个像素 ==========")

        for i in range(20):
            r = i // 254
            c = i % 254

            print(
                f"[{r:3d},{c:3d}] "
                f"FPGA={fpga_array[r, c]:3d}   "
                f"理论={fpga_reference[r, c]:3d}   "
                f"差={error[r, c]:+d}"
            )
