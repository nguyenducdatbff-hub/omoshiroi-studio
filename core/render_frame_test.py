from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math

def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color, outline_width=6):
    x, y = pos
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw fill
    draw.text((x, y), text, font=font, fill=fill_color)

def test_frame():
    W, H = 1080, 1920
    
    # Load background
    bg_path = "irasutoya_shorts_generator/assets/backgrounds/room_japan.jpg"
    bg = Image.open(bg_path).resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
    
    # Add slight dark vignette at top and bottom for readability
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    # Top banner gradient
    for y in range(450):
        alpha = int(180 * (1.0 - y / 450.0))
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        
    # Subtitle area subtle dark gradient
    for y in range(1000, 1500):
        rel = (y - 1000) / 250.0 if y < 1250 else (1500 - y) / 250.0
        alpha = int(100 * max(0.0, rel))
        ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
        
    frame = Image.alpha_composite(bg, overlay)
    
    # Load characters
    char_h = 1100
    boy_img = Image.open("irasutoya_shorts_generator/assets/characters/boy_normal.png").convert("RGBA")
    aspect = boy_img.width / boy_img.height
    boy_w = int(char_h * aspect)
    boy_img = boy_img.resize((boy_w, char_h), Image.Resampling.LANCZOS)
    
    girl_img = Image.open("irasutoya_shorts_generator/assets/characters/girl_blazer.png").convert("RGBA")
    aspect_g = girl_img.width / girl_img.height
    girl_w = int(char_h * aspect_g)
    girl_img = girl_img.resize((girl_w, char_h), Image.Resampling.LANCZOS)
    
    # Boy on left, Girl on right
    # Girl is speaking, so she bounces slightly up by 25px
    boy_pos = (80, H - char_h - 80)
    girl_pos = (W - girl_w - 80, H - char_h - 80 - 30) # hopped up
    
    frame.paste(boy_img, boy_pos, boy_img)
    frame.paste(girl_img, girl_pos, girl_img)
    
    # Draw Headers
    draw = ImageDraw.Draw(frame)
    
    font_dela_big = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_dela.ttf", 95)
    font_dela_sub = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_dela.ttf", 60)
    font_sub = ImageFont.truetype("irasutoya_shorts_generator/assets/fonts/font_zenmaru.ttf", 72)
    
    # Top 1: "サクッと笑える"
    title1 = "サクッと笑える"
    bbox1 = font_dela_big.getbbox(title1)
    t1_w = bbox1[2] - bbox1[0]
    t1_x = (W - t1_w) // 2
    # Outer black stroke, golden yellow fill
    draw_text_with_outline(draw, (t1_x, 80), title1, font_dela_big, (255, 225, 50), (0, 0, 0), outline_width=10)
    
    # Top 2: "意味が分かると"
    title2 = "意味が分かると"
    bbox2 = font_dela_sub.getbbox(title2)
    t2_w = bbox2[2] - bbox2[0]
    t2_x = (W - t2_w) // 2
    draw_text_with_outline(draw, (t2_x, 210), title2, font_dela_sub, (255, 255, 255), (0, 0, 0), outline_width=8)
    
    # Subtitle text: "生理的に無理かな！"
    sub_text = "生理的に無理かな！"
    bbox_sub = font_sub.getbbox(sub_text)
    sub_w = bbox_sub[2] - bbox_sub[0]
    sub_x = (W - sub_w) // 2
    # Girl subtitle: White text with deep magenta/pink outline
    draw_text_with_outline(draw, (sub_x, 1180), sub_text, font_sub, (255, 255, 255), (200, 20, 80), outline_width=10)
    
    os.makedirs("irasutoya_shorts_generator/output", exist_ok=True)
    frame.save("irasutoya_shorts_generator/output/test_frame.png")
    print("Saved test_frame.png successfully!")

test_frame()
