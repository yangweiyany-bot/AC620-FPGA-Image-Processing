from pathlib import Path
from PIL import Image
import numpy as np

# ============================================================
# 参数
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "gray_256x256.png"

OUTPUT_IMAGE = OUTPUT_DIR / "noisy_256x256.png"
OUTPUT_BIN = OUTPUT_DIR / "noisy_256x256.bin"

NOISE_RATIO = 0.05      # 5% 椒盐噪声


# ============================================================
# 读取原始灰度图
# ============================================================

img = Image.open(INPUT_FILE).convert("L")

if img.size != (256, 256):
    raise ValueError(
        f"输入图片必须是 256x256，当前尺寸为 {img.size}"
    )

image = np.array(img, dtype=np.uint8)

# 固定随机种子，保证每次实验完全一样
rng = np.random.default_rng(2026)

noisy = image.copy()


# ============================================================
# 添加椒盐噪声
# ============================================================

total_pixels = 256 * 256
noise_pixels = int(total_pixels * NOISE_RATIO)

# 随机选择不重复的像素
indices = rng.choice(
    total_pixels,
    size=noise_pixels,
    replace=False
)

rows = indices // 256
cols = indices % 256

# 一半设为黑色，一半设为白色
half = noise_pixels // 2

noisy[rows[:half], cols[:half]] = 0
noisy[rows[half:], cols[half:]] = 255


# ============================================================
# 保存
# ============================================================

Image.fromarray(noisy).save(OUTPUT_IMAGE)

OUTPUT_BIN.write_bytes(noisy.tobytes())


# ============================================================
# 输出信息
# ============================================================

print("========== 椒盐噪声测试图生成完成 ==========")
print()
print("原始图片：", INPUT_FILE)
print("噪声比例：", f"{NOISE_RATIO * 100:.1f}%")
print("噪声像素：", noise_pixels)
print()
print("噪声图片：", OUTPUT_IMAGE)
print("FPGA输入：", OUTPUT_BIN)
print("BIN字节数：", OUTPUT_BIN.stat().st_size)

if OUTPUT_BIN.stat().st_size == 256 * 256:
    print()
    print("NOISE_IMAGE_GENERATION_PASS")
