from PIL import Image, ImageDraw, ImageFont
import time
import os

W, H = 1080, 1920
# Benchmark Pillow paste speed with pre-cached elements
bg = Image.open("irasutoya_shorts_generator/assets/backgrounds/room_japan.jpg").resize((W, H)).convert("RGBA")
boy = Image.open("irasutoya_shorts_generator/assets/characters/boy_normal.png").convert("RGBA")
aspect_b = boy.width / boy.height
boy = boy.resize((int(1350 * aspect_b), 1350))

girl = Image.open("irasutoya_shorts_generator/assets/characters/girl_blazer.png").convert("RGBA")
aspect_g = girl.width / girl.height
girl = girl.resize((int(1350 * aspect_g), 1350))

start = time.time()
for i in range(100):
    frame = bg.copy()
    frame.paste(boy, (40, 650), boy)
    frame.paste(girl, (W - girl.width - 40, 650 - (i % 20)), girl)
    _ = frame.tobytes()

elapsed = time.time() - start
print(f"100 frames rendered in {elapsed:.3f}s -> {100/elapsed:.1f} fps")
