from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def draw_text_with_glow(draw, pos, text, font, fill_color, stroke_color, glow_color, stroke_w=8, glow_w=18):
    x, y = pos
    # Outer soft glow
    if glow_color and glow_w > 0:
        for dx in range(-glow_w, glow_w + 1, 3):
            for dy in range(-glow_w, glow_w + 1, 3):
                if dx * dx + dy * dy <= glow_w * glow_w:
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    # Inner sharp stroke
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx * dx + dy * dy <= stroke_w * stroke_w:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # Main text fill
    draw.text((x, y), text, font=font, fill=fill_color)

def test_frame_v2():
    W, H = 1080, 1920
    
    bg_path = "irasutoya_shorts_generator/assets/backgrounds/room_japan.jpg"
    bg = Image.open(bg_path).resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    
    # Vignette
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for y in range(400):
        alpha = int(190 * (1.0 - y / 400.0))
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    frame = Image.alpha_composite(bg, overlay)
    
    # Characters: 3/4 framing (scale height to 1450)
    char_h = 1450
    boy_img = Image.open("irasutoya_shorts_generator/assets/characters/boy_normal.png").convert("RGBA")
    aspect = boy_img.width / boy_img.height
    boy_w = int(char_h * aspect)
    boy_img = boy_img.resize((boy_w, char_h), Image.Resampling.LANCZOS)
    
    girl_img = Image.open("irasutoya_shorts_generator/assets/characters/girl_blazer.png").convert("RGBA")
    aspect_g = girl_img.width / girl_img.height
    girl_w = int(char_h * aspect_g)
    girl_img = girl_img.resize((girl_w, char_h), Image.Resampling.LANCZOS)
    
    # Position: heads around y=550, bodies extend to bottom
    # Girl is speaking -> hopped up 35px
    boy_pos = (50, 520)
    girl_pos = (W - girl_w - 50, 520 - 35)
    
    frame.paste(boy_img, boy_pos, boy_img)
    frame.paste(girl_img, girl_pos, girl_img)
    
    draw = ImageDraw.Draw(frame)
    font_dela_big = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_dela.ttf", 105)
    font_dela_sub = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_dela.ttf", 68)
    font_sub = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_zenmaru.ttf", 78)
    
    # 1. Main Header: "サクッと笑える"
    title1 = "サクッと笑える"
    bbox1 = font_dela_big.getbbox(title1)
    t1_w = bbox1[2] - bbox1[0]
    t1_x = (W - t1_w) // 2
    draw_text_with_glow(draw, (t1_x, 90), title1, font_dela_big,
                        fill_color=(255, 230, 60),
                        stroke_color=(0, 0, 0),
                        glow_color=(255, 255, 200, 180),
                        stroke_w=10, glow_w=20)
                        
    # 2. Subtitle Banner: "意味が分かると"
    title2 = "意味が分かると"
    bbox2 = font_dela_sub.getbbox(title2)
    t2_w = bbox2[2] - bbox2[0]
    t2_x = (W - t2_w) // 2
    draw_text_with_glow(draw, (t2_x, 230), title2, font_dela_sub,
                        fill_color=(255, 255, 255),
                        stroke_color=(0, 0, 0),
                        glow_color=None,
                        stroke_w=9, glow_w=0)
                        
    # 3. Speech Subtitle: "生理的に無理かな！"
    sub_text = "生理的に無理かな！"
    bbox_sub = font_sub.getbbox(sub_text)
    sub_w = bbox_sub[2] - bbox_sub[0]
    sub_x = (W - sub_w) // 2
    # Upper-middle position near the talking girl
    draw_text_with_glow(draw, (sub_x, 420), sub_text, font_sub,
                        fill_color=(255, 255, 255),
                        stroke_color=(220, 20, 90),
                        glow_color=(0, 0, 0, 200),
                        stroke_w=12, glow_w=18)
                        
    frame.save("irasutoya_shorts_generator/output/test_frame_v2.png")
    print("Saved test_frame_v2.png")

test_frame_v2()
