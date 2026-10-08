from PIL import Image, ImageFilter
import numpy as np
from pathlib import Path

# =========================
# 路径设置
# =========================
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# 找到 input 中的图片
# =========================
image_files = []

for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
    image_files.extend(INPUT_DIR.glob(ext))

if not image_files:
    print("没有找到图片！")
    print("请先把一张图片放入：")
    print(INPUT_DIR)
    input("按回车退出...")
    raise SystemExit

image_path = image_files[0]

print("读取图片：", image_path.name)

# =========================
# 读取原图
# =========================
original = Image.open(image_path).convert("RGB")

# =========================
# 缩放到 256 × 256
# =========================
resized = original.resize((256, 256))

# =========================
# 转换为 8 位灰度图
# 每个像素范围：0~255
# =========================
gray = resized.convert("L")

# =========================
# 转成 numpy 数组
# =========================
gray_array = np.array(gray, dtype=np.uint8)

print()
print("灰度图尺寸：", gray_array.shape)
print("数据类型：", gray_array.dtype)
print("最小灰度值：", gray_array.min())
print("最大灰度值：", gray_array.max())
print("像素总数：", gray_array.size)

# =========================
# 保存灰度图
# =========================
gray.save(OUTPUT_DIR / "gray_256x256.png")

# =========================
# 保存 FPGA 可以接收的原始二进制
# =========================
gray_array.tofile(OUTPUT_DIR / "gray_256x256.bin")

# =========================
# 生成 3×3 均值滤波参考图
# =========================
mean_img = gray.filter(ImageFilter.BoxBlur(1))
mean_img.save(OUTPUT_DIR / "mean_3x3_reference.png")

# =========================
# 生成 3×3 中值滤波参考图
# =========================
median_img = gray.filter(ImageFilter.MedianFilter(size=3))
median_img.save(OUTPUT_DIR / "median_3x3_reference.png")

print()
print("处理完成！")
print("输出目录：", OUTPUT_DIR)
print()
print("生成文件：")
print("1. gray_256x256.png")
print("2. gray_256x256.bin")
print("3. mean_3x3_reference.png")
print("4. median_3x3_reference.png")

# =========================
# 显示图片
# =========================
original.show(title="Original")
gray.show(title="Gray 256x256")
mean_img.show(title="Mean 3x3")
median_img.show(title="Median 3x3")
